"""Clinical Calculation Engine: Safe, Deterministic AST-based formula parser and evaluator for derived analytes."""
from __future__ import annotations

import ast
from decimal import Decimal, ROUND_HALF_UP, DivisionByZero, InvalidOperation
from typing import Any

from sqlalchemy.orm import Session

from app.audit.service import log_audit_event
from app.errors import ConflictError, NotFoundError, ValidationError
from app.models.pathology import OrderItem, Result, ResultValue, Test, TestReferenceRange
from app.pathology.reference_range_service import evaluate_result_against_range, resolve_reference_range
from app.security.tenant_guard import TenantContext, verify_tenant_boundary


class CalculationEngineError(ValidationError):
    """Base error for formula parsing and calculation."""
    pass


class CalculationSyntaxError(CalculationEngineError):
    """Raised when calculation formula has invalid syntax."""
    pass


class CalculationMissingVariableError(CalculationEngineError):
    """Raised when an analyte required by the formula is missing."""
    pass


class CalculationEvaluationError(CalculationEngineError):
    """Raised when formula evaluation fails (e.g. division by zero)."""
    pass


SAFE_FUNCTIONS = {
    "min": min,
    "max": max,
    "abs": abs,
    "round": lambda x, p=2: round(x, int(p)),
}


class _SafeEvaluator(ast.NodeVisitor):
    def __init__(self, variables: dict[str, Decimal]):
        self.variables = {k.strip().upper(): v for k, v in variables.items()}

    def visit(self, node: ast.AST) -> Decimal:
        method_name = f"visit_{node.__class__.__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ast.AST) -> Any:
        raise CalculationSyntaxError(f"Unsupported syntax construct: {node.__class__.__name__}")

    def visit_Expression(self, node: ast.Expression) -> Decimal:
        return self.visit(node.body)

    def visit_Constant(self, node: ast.Constant) -> Decimal:
        if isinstance(node.value, (int, float)):
            return Decimal(str(node.value))
        raise CalculationSyntaxError(f"Non-numeric constant '{node.value}' is not allowed in formula")

    def visit_Num(self, node: ast.Num) -> Decimal:
        return Decimal(str(node.n))

    def visit_Name(self, node: ast.Name) -> Decimal:
        var_name = node.id.strip().upper()
        if var_name not in self.variables:
            raise CalculationMissingVariableError(f"Missing required analyte/variable '{var_name}' for calculation")
        val = self.variables[var_name]
        if val is None:
            raise CalculationMissingVariableError(f"Value for analyte '{var_name}' is None/null")
        return Decimal(str(val))

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Decimal:
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.UAdd):
            return operand
        if isinstance(node.op, ast.USub):
            return -operand
        raise CalculationSyntaxError(f"Unsupported unary operator: {node.op.__class__.__name__}")

    def visit_BinOp(self, node: ast.BinOp) -> Decimal:
        left = self.visit(node.left)
        right = self.visit(node.right)

        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            if right == Decimal("0"):
                raise CalculationEvaluationError("Division by zero in formula evaluation")
            try:
                return left / right
            except (DivisionByZero, InvalidOperation) as e:
                raise CalculationEvaluationError(f"Division error: {e}")
        if isinstance(node.op, ast.Pow):
            try:
                return left ** right
            except Exception as e:
                raise CalculationEvaluationError(f"Power evaluation error: {e}")
        raise CalculationSyntaxError(f"Unsupported binary operator: {node.op.__class__.__name__}")

    def visit_Call(self, node: ast.Call) -> Decimal:
        if not isinstance(node.func, ast.Name):
            raise CalculationSyntaxError("Dynamic function invocation is not allowed")
        fn_name = node.func.id.lower()
        if fn_name not in SAFE_FUNCTIONS:
            raise CalculationSyntaxError(f"Function '{fn_name}' is not in safe function whitelist")
        args = [self.visit(arg) for arg in node.args]
        try:
            res = SAFE_FUNCTIONS[fn_name](*args)
            return Decimal(str(res))
        except Exception as e:
            raise CalculationEvaluationError(f"Error executing function '{fn_name}': {e}")


def extract_formula_variables(formula: str) -> set[str]:
    """Parse formula and return set of referenced variable/analyte codes."""
    clean = (formula or "").strip()
    if not clean:
        return set()
    try:
        parsed = ast.parse(clean, mode="eval")
    except SyntaxError as e:
        raise CalculationSyntaxError(f"Syntax error in formula '{formula}': {e}")

    vars_found: set[str] = set()
    for node in ast.walk(parsed):
        if isinstance(node, ast.Name):
            name_val = node.id.strip().upper()
            if name_val.lower() not in SAFE_FUNCTIONS:
                vars_found.add(name_val)
    return vars_found


def evaluate_formula(
    formula: str,
    variables: dict[str, float | Decimal],
    precision: int = 2,
) -> Decimal:
    """
    Safely and deterministically evaluate a clinical mathematical formula.
    Result is rounded to `precision` decimal places using ROUND_HALF_UP.
    """
    clean = (formula or "").strip()
    if not clean:
        raise CalculationSyntaxError("Empty formula cannot be evaluated")

    try:
        parsed = ast.parse(clean, mode="eval")
    except SyntaxError as e:
        raise CalculationSyntaxError(f"Syntax error in formula '{formula}': {e}")

    dec_vars = {k: Decimal(str(v)) for k, v in variables.items() if v is not None}
    evaluator = _SafeEvaluator(dec_vars)
    raw_result = evaluator.visit(parsed)

    quantizer = Decimal("1") if precision <= 0 else Decimal("10") ** -precision
    return raw_result.quantize(quantizer, rounding=ROUND_HALF_UP)



def compute_derived_results(
    db: Session,
    *,
    tenant_context: TenantContext,
    result_id: str,
    actor_user_id: str | None = None,
) -> list[ResultValue]:
    """
    Find calculated tests / analytes for the result's order item, execute their formulas,
    and persist derived ResultValue entries with flags and audit logging.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id
    effective_user_id = actor_user_id or tenant_context.user_id

    result = db.query(Result).filter(Result.id == result_id, Result.tenant_id == tenant_id).first()
    if not result:
        raise NotFoundError(f"Result '{result_id}' not found")

    order_item = result.order_item
    order = order_item.order
    patient = order.patient if hasattr(order, "patient") and order.patient else db.query(OrderItem).filter(OrderItem.id == order_item.id).first()

    # Collect existing values as variables dict
    existing_vars: dict[str, Decimal] = {}
    for rv in result.values:
        if rv.numeric_value is not None:
            existing_vars[rv.analyte_code.upper()] = rv.numeric_value

    calculated_tests: list[Test] = []
    if order_item.test and order_item.test.is_calculated and order_item.test.calculation_formula:
        calculated_tests.append(order_item.test)

    # Also check if order_item belongs to an order with other calculated items in the same order
    sibling_items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    for sib in sibling_items:
        if sib.test and sib.test.is_calculated and sib.test.calculation_formula and sib.test not in calculated_tests:
            calculated_tests.append(sib.test)

    updated_values: list[ResultValue] = []

    for c_test in calculated_tests:
        formula = c_test.calculation_formula
        if not formula:
            continue

        try:
            computed_num = evaluate_formula(
                formula,
                existing_vars,
                precision=c_test.decimal_precision if c_test.decimal_precision is not None else 2,
            )
        except CalculationMissingVariableError:
            # Cannot calculate yet if required variable is missing; skip
            continue

        existing_val_entry = next((v for v in result.values if v.analyte_code.upper() == c_test.code.upper()), None)

        # Resolve reference range for calculated test
        ref_range = resolve_reference_range(
            db,
            tenant_context=tenant_context,
            test_id=c_test.id,
            patient_sex=order.patient_id,  # sex lookup if available
            as_of=result.created_at,
        )
        abnormal_flag = "normal"
        critical_flag = False
        ref_text = None
        if ref_range:
            eval_res = evaluate_result_against_range(ref_range, computed_num)
            abnormal_flag = eval_res["flag"]
            critical_flag = eval_res["is_critical"]
            ref_text = ref_range.text_range

        if existing_val_entry:
            existing_val_entry.numeric_value = computed_num
            existing_val_entry.raw_value = str(computed_num)
            existing_val_entry.abnormal_flag = abnormal_flag
            existing_val_entry.critical_flag = critical_flag
            existing_val_entry.reference_text = ref_text
            existing_val_entry.reference_range_id = ref_range.id if ref_range else None
            updated_values.append(existing_val_entry)
        else:
            new_val = ResultValue(
                result_id=result.id,
                analyte_code=c_test.code.upper(),
                analyte_name=c_test.name,
                raw_value=str(computed_num),
                numeric_value=computed_num,
                unit=c_test.unit,
                reference_text=ref_text,
                reference_range_id=ref_range.id if ref_range else None,
                abnormal_flag=abnormal_flag,
                critical_flag=critical_flag,
                notes="Calculated automatically by formula engine",
            )
            db.add(new_val)
            updated_values.append(new_val)

        existing_vars[c_test.code.upper()] = computed_num

    db.flush()

    if updated_values:
        log_audit_event(
            db,
            tenant_id=tenant_id,
            action_code="calculation.executed",
            actor_user_id=effective_user_id,
            entity_type="result",
            entity_id=result.id,
            after_json={"calculated_count": len(updated_values)},
        )
        db.commit()

    return updated_values


"""Tests for P05-03: Clinical Calculation Engine (Deterministic AST formulas, derived analytes, security, and audit)."""
import uuid
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.audit.service import get_audit_logs
from app.db import Base
from app.models.core import Branch, Department, Tenant
from app.models.identity import Permission, Role, RolePermission, User, UserRole
from app.models.pathology import Order, OrderItem, Result, ResultValue, Test
from app.models.patient import Patient
from app.pathology.calculation_engine import (
    CalculationEvaluationError,
    CalculationMissingVariableError,
    CalculationSyntaxError,
    compute_derived_results,
    evaluate_formula,
    extract_formula_variables,
)
from app.pathology.order_workflow import create_order
from app.pathology.reference_range_service import add_reference_range
from app.pathology.result_service import record_result_values
from app.pathology.test_master import create_test
from app.patient.service import register_patient
from app.security.tenant_guard import TenantContext


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_deterministic_clinical_formulas():
    # 1. Friedewald LDL: LDL = CHOL - HDL - (TRIG / 5)
    ldl = evaluate_formula(
        "CHOL - HDL - (TRIG / 5)",
        {"CHOL": 200, "HDL": 50, "TRIG": 150},
        precision=1,
    )
    # 200 - 50 - 30 = 120.0
    assert ldl == Decimal("120.0")

    # 2. Globulin: GLOB = TP - ALB
    glob = evaluate_formula(
        "TP - ALB",
        {"TP": 7.4, "ALB": 4.2},
        precision=2,
    )
    # 7.4 - 4.2 = 3.20
    assert glob == Decimal("3.20")

    # 3. A/G Ratio: AG_RATIO = ALB / (TP - ALB)
    ag_ratio = evaluate_formula(
        "round(ALB / (TP - ALB), 2)",
        {"TP": 7.4, "ALB": 4.2},
        precision=2,
    )
    # 4.2 / 3.2 = 1.3125 -> 1.31
    assert ag_ratio == Decimal("1.31")

    # 4. Anion Gap: NA - (CL + HCO3)
    anion_gap = evaluate_formula(
        "NA - (CL + HCO3)",
        {"NA": 140, "CL": 102, "HCO3": 24},
        precision=0,
    )
    # 140 - (102 + 24) = 14
    assert anion_gap == Decimal("14")

    # 5. Corrected Calcium: TOTAL_CA + 0.8 * (4.0 - ALB)
    corr_ca = evaluate_formula(
        "TOTAL_CA + 0.8 * (4.0 - ALB)",
        {"TOTAL_CA": 8.0, "ALB": 3.0},
        precision=2,
    )
    # 8.0 + 0.8 * 1.0 = 8.80
    assert corr_ca == Decimal("8.80")


def test_formula_variable_extraction():
    vars_found = extract_formula_variables("CHOL - HDL - (TRIG / 5)")
    assert vars_found == {"CHOL", "HDL", "TRIG"}

    vars_ratio = extract_formula_variables("round(ALB / (TP - ALB), 2)")
    assert vars_ratio == {"ALB", "TP"}


def test_safety_and_error_handling():
    # 1. Division by zero
    with pytest.raises(CalculationEvaluationError):
        evaluate_formula("100 / 0", {})

    # 2. Missing required variable
    with pytest.raises(CalculationMissingVariableError):
        evaluate_formula("CHOL - HDL", {"CHOL": 150})

    # 3. Security: Code injection / arbitrary execution attempts rejected
    with pytest.raises(CalculationSyntaxError):
        evaluate_formula("__import__('os').system('dir')", {})

    with pytest.raises(CalculationSyntaxError):
        evaluate_formula("open('/etc/passwd').read()", {})

    with pytest.raises(CalculationSyntaxError):
        evaluate_formula("lambda x: x", {})


def test_compute_derived_results_end_to_end(db_session: Session):
    tenant = Tenant(name="Precision Lab", code="PL-01", is_active=True)
    db_session.add(tenant)
    db_session.flush()

    branch = Branch(tenant_id=tenant.id, name="Main Lab", code="ML-01", is_active=True)
    db_session.add(branch)
    db_session.flush()

    dept = Department(tenant_id=tenant.id, branch_id=branch.id, name="Biochemistry", code="BIO", is_active=True)
    db_session.add(dept)
    db_session.flush()

    # Permissions
    perms = [
        Permission(code="result.view", module="pathology", resource="result", action="view", risk_level="normal"),
        Permission(code="result.enter", module="pathology", resource="result", action="enter", risk_level="normal"),
        Permission(code="order.create", module="pathology", resource="order", action="create", risk_level="normal"),
        Permission(code="patient.register", module="patient", resource="patient", action="register", risk_level="normal"),
        Permission(code="test.create", module="pathology", resource="test", action="create", risk_level="normal"),
    ]
    db_session.add_all(perms)
    db_session.flush()

    role = Role(tenant_id=tenant.id, name="Lab Tech", is_system=False)
    db_session.add(role)
    db_session.flush()
    for p in perms:
        db_session.add(RolePermission(role_id=role.id, permission_id=p.id, allow=True))

    user = User(tenant_id=tenant.id, email="tech@precision.com", username="tech_p", hashed_password="pw")
    db_session.add(user)
    db_session.flush()
    db_session.add(UserRole(user_id=user.id, role_id=role.id))

    ctx = TenantContext(tenant_id=tenant.id, branch_id=branch.id, user_id=user.id)

    # 1. Base test: Total Protein
    test_tp = create_test(
        db_session,
        tenant_context=ctx,
        code="TP",
        name="Total Protein",
        display_name="Total Protein",
        unit="g/dL",
        department_id=dept.id,
    )
    # 2. Base test: Albumin
    test_alb = create_test(
        db_session,
        tenant_context=ctx,
        code="ALB",
        name="Albumin",
        display_name="Albumin",
        unit="g/dL",
        department_id=dept.id,
    )
    # 3. Calculated test: Globulin = TP - ALB
    test_glob = create_test(
        db_session,
        tenant_context=ctx,
        code="GLOB",
        name="Globulin",
        display_name="Globulin",
        unit="g/dL",
        department_id=dept.id,
        is_calculated=True,
        calculation_formula="TP - ALB",
        decimal_precision=2,
    )
    add_reference_range(
        db_session,
        tenant_context=ctx,
        test_id=test_glob.id,
        sex="all",
        low_value=2.0,
        high_value=3.5,
        text_range="2.0 - 3.5 g/dL",
    )

    # Register patient & Order
    pat = register_patient(
        db_session,
        tenant_context=ctx,
        first_name="Marie",
        last_name="Curie",
        sex="female",
    )
    order = create_order(
        db_session,
        tenant_context=ctx,
        patient_id=pat.id,
        test_ids=[test_tp.id, test_alb.id, test_glob.id],
        branch_id=branch.id,
    )
    item_tp = next(it for it in order.items if it.test_id == test_tp.id)

    # Enter TP and ALB values
    res = record_result_values(
        db_session,
        tenant_context=ctx,
        order_item_id=item_tp.id,
        status="entered",
        values=[
            {"analyte_code": "TP", "raw_value": "7.5"},
            {"analyte_code": "ALB", "raw_value": "4.5"},
        ],
    )

    # Compute derived results
    derived = compute_derived_results(
        db_session,
        tenant_context=ctx,
        result_id=res.id,
    )
    assert len(derived) == 1
    glob_val = derived[0]
    assert glob_val.analyte_code == "GLOB"
    # 7.5 - 4.5 = 3.00 (within 2.0 - 3.5)
    assert float(glob_val.numeric_value) == 3.00
    assert glob_val.abnormal_flag == "normal"
    assert not glob_val.critical_flag

    # Verify audit event
    logs = get_audit_logs(db_session, tenant_id=ctx.tenant_id, entity_type="result", entity_id=res.id)
    assert any(l.action_code == "calculation.executed" for l in logs)


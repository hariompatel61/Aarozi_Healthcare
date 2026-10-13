"""Reference Range Service: Age, Sex, Context-specific reference range management and clinical resolution."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session

from app.audit.service import log_audit_event
from app.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.identity import User
from app.models.pathology import Test, TestReferenceRange
from app.rbac.engine import authorize_action
from app.security.tenant_guard import TenantContext, verify_tenant_boundary


VALID_SEXES = {"all", "male", "female", "other"}
VALID_AGE_UNITS = {"years", "months", "days"}


def _check_permission(
    db: Session,
    *,
    tenant_context: TenantContext,
    permission_code: str,
    actor_user_id: str | None = None,
) -> None:
    user_id = actor_user_id or tenant_context.user_id
    if not user_id:
        return
    user = db.query(User).filter(User.id == user_id, User.tenant_id == tenant_context.tenant_id).first()
    if user and not authorize_action(db, user, permission_code, branch_id=tenant_context.branch_id):
        raise ForbiddenError(f"User is not authorized for '{permission_code}'")


def validate_reference_range_inputs(
    *,
    sex: str = "all",
    age_unit: str = "years",
    age_min: float | Decimal | None = None,
    age_max: float | Decimal | None = None,
    low_value: float | Decimal | None = None,
    high_value: float | Decimal | None = None,
    critical_low: float | Decimal | None = None,
    critical_high: float | Decimal | None = None,
) -> None:
    clean_sex = (sex or "all").strip().lower()
    if clean_sex not in VALID_SEXES:
        raise ValidationError(f"Invalid sex '{sex}'. Must be one of: {sorted(list(VALID_SEXES))}", field="sex")

    clean_unit = (age_unit or "years").strip().lower()
    if clean_unit not in VALID_AGE_UNITS:
        raise ValidationError(f"Invalid age_unit '{age_unit}'. Must be one of: {sorted(list(VALID_AGE_UNITS))}", field="age_unit")

    a_min = Decimal(str(age_min)) if age_min is not None else None
    a_max = Decimal(str(age_max)) if age_max is not None else None

    if a_min is not None and a_min < Decimal("0"):
        raise ValidationError("age_min cannot be negative", field="age_min")
    if a_max is not None and a_max < Decimal("0"):
        raise ValidationError("age_max cannot be negative", field="age_max")
    if a_min is not None and a_max is not None and a_min > a_max:
        raise ValidationError("age_min cannot be greater than age_max", field="age_min")

    v_low = Decimal(str(low_value)) if low_value is not None else None
    v_high = Decimal(str(high_value)) if high_value is not None else None
    c_low = Decimal(str(critical_low)) if critical_low is not None else None
    c_high = Decimal(str(critical_high)) if critical_high is not None else None

    if v_low is not None and v_high is not None and v_low > v_high:
        raise ValidationError("low_value cannot be greater than high_value", field="low_value")

    if c_low is not None and v_low is not None and c_low > v_low:
        raise ValidationError("critical_low cannot be greater than low_value", field="critical_low")

    if c_high is not None and v_high is not None and c_high < v_high:
        raise ValidationError("critical_high cannot be less than high_value", field="critical_high")


def _get_test_in_tenant(db: Session, tenant_id: str, test_id: str) -> Test:
    test = db.query(Test).filter(Test.id == test_id, Test.tenant_id == tenant_id).first()
    if not test:
        raise NotFoundError(f"Test '{test_id}' not found")
    return test


def add_reference_range(
    db: Session,
    *,
    tenant_context: TenantContext,
    test_id: str,
    sex: str = "all",
    age_min: float | Decimal | None = None,
    age_max: float | Decimal | None = None,
    age_unit: str = "years",
    context: str | None = None,
    priority: int = 100,
    low_value: float | Decimal | None = None,
    high_value: float | Decimal | None = None,
    critical_low: float | Decimal | None = None,
    critical_high: float | Decimal | None = None,
    text_range: str | None = None,
    effective_from: datetime | None = None,
    effective_to: datetime | None = None,
    actor_user_id: str | None = None,
) -> TestReferenceRange:
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    _check_permission(db, tenant_context=tenant_context, permission_code="test.create", actor_user_id=actor_user_id)

    test = _get_test_in_tenant(db, tenant_context.tenant_id, test_id)

    validate_reference_range_inputs(
        sex=sex,
        age_unit=age_unit,
        age_min=age_min,
        age_max=age_max,
        low_value=low_value,
        high_value=high_value,
        critical_low=critical_low,
        critical_high=critical_high,
    )

    clean_context = context.strip().lower() if context else None
    now_ts = effective_from or datetime.now(timezone.utc)

    rr = TestReferenceRange(
        test_id=test.id,
        sex=(sex or "all").strip().lower(),
        age_min=Decimal(str(age_min)) if age_min is not None else None,
        age_max=Decimal(str(age_max)) if age_max is not None else None,
        age_unit=(age_unit or "years").strip().lower(),
        context=clean_context,
        priority=priority,
        low_value=Decimal(str(low_value)) if low_value is not None else None,
        high_value=Decimal(str(high_value)) if high_value is not None else None,
        critical_low=Decimal(str(critical_low)) if critical_low is not None else None,
        critical_high=Decimal(str(critical_high)) if critical_high is not None else None,
        text_range=text_range.strip() if text_range else None,
        effective_from=now_ts,
        effective_to=effective_to,
    )
    db.add(rr)
    db.flush()

    log_audit_event(
        db,
        tenant_id=tenant_context.tenant_id,
        action_code="reference_range.created",
        actor_user_id=actor_user_id or tenant_context.user_id,
        entity_type="test_reference_range",
        entity_id=rr.id,
        after_json={
            "test_id": test.id,
            "sex": rr.sex,
            "context": rr.context,
            "age_min": float(rr.age_min) if rr.age_min is not None else None,
            "age_max": float(rr.age_max) if rr.age_max is not None else None,
            "low_value": float(rr.low_value) if rr.low_value is not None else None,
            "high_value": float(rr.high_value) if rr.high_value is not None else None,
        },
    )

    db.commit()
    db.refresh(rr)
    return rr



def update_reference_range(
    db: Session,
    *,
    tenant_context: TenantContext,
    reference_range_id: str,
    update_data: dict[str, Any],
    actor_user_id: str | None = None,
) -> TestReferenceRange:
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    _check_permission(db, tenant_context=tenant_context, permission_code="test.edit", actor_user_id=actor_user_id)

    rr = db.query(TestReferenceRange).filter(TestReferenceRange.id == reference_range_id).first()
    if not rr:
        raise NotFoundError(f"Reference range '{reference_range_id}' not found")

    _get_test_in_tenant(db, tenant_context.tenant_id, rr.test_id)

    new_sex = update_data.get("sex", rr.sex)
    new_age_unit = update_data.get("age_unit", rr.age_unit)
    new_age_min = update_data.get("age_min", rr.age_min)
    new_age_max = update_data.get("age_max", rr.age_max)
    new_low = update_data.get("low_value", rr.low_value)
    new_high = update_data.get("high_value", rr.high_value)
    new_c_low = update_data.get("critical_low", rr.critical_low)
    new_c_high = update_data.get("critical_high", rr.critical_high)

    validate_reference_range_inputs(
        sex=new_sex,
        age_unit=new_age_unit,
        age_min=new_age_min,
        age_max=new_age_max,
        low_value=new_low,
        high_value=new_high,
        critical_low=new_c_low,
        critical_high=new_c_high,
    )

    before_snapshot = {
        "sex": rr.sex,
        "context": rr.context,
        "low_value": float(rr.low_value) if rr.low_value is not None else None,
        "high_value": float(rr.high_value) if rr.high_value is not None else None,
    }

    if "sex" in update_data:
        rr.sex = (new_sex or "all").strip().lower()
    if "age_unit" in update_data:
        rr.age_unit = (new_age_unit or "years").strip().lower()
    if "age_min" in update_data:
        rr.age_min = Decimal(str(new_age_min)) if new_age_min is not None else None
    if "age_max" in update_data:
        rr.age_max = Decimal(str(new_age_max)) if new_age_max is not None else None
    if "context" in update_data:
        ctx_val = update_data["context"]
        rr.context = ctx_val.strip().lower() if ctx_val else None
    if "priority" in update_data:
        rr.priority = int(update_data["priority"])
    if "low_value" in update_data:
        rr.low_value = Decimal(str(new_low)) if new_low is not None else None
    if "high_value" in update_data:
        rr.high_value = Decimal(str(new_high)) if new_high is not None else None
    if "critical_low" in update_data:
        rr.critical_low = Decimal(str(new_c_low)) if new_c_low is not None else None
    if "critical_high" in update_data:
        rr.critical_high = Decimal(str(new_c_high)) if new_c_high is not None else None
    if "text_range" in update_data:
        txt = update_data["text_range"]
        rr.text_range = txt.strip() if txt else None

    log_audit_event(
        db,
        tenant_id=tenant_context.tenant_id,
        action_code="reference_range.updated",
        actor_user_id=actor_user_id or tenant_context.user_id,
        entity_type="test_reference_range",
        entity_id=rr.id,
        before_json=before_snapshot,
        after_json={
            "sex": rr.sex,
            "context": rr.context,
            "low_value": float(rr.low_value) if rr.low_value is not None else None,
            "high_value": float(rr.high_value) if rr.high_value is not None else None,
        },
    )

    db.commit()
    db.refresh(rr)
    return rr


def delete_reference_range(
    db: Session,
    *,
    tenant_context: TenantContext,
    reference_range_id: str,
    actor_user_id: str | None = None,
) -> None:
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    _check_permission(db, tenant_context=tenant_context, permission_code="test.edit", actor_user_id=actor_user_id)

    rr = db.query(TestReferenceRange).filter(TestReferenceRange.id == reference_range_id).first()
    if not rr:
        raise NotFoundError(f"Reference range '{reference_range_id}' not found")

    _get_test_in_tenant(db, tenant_context.tenant_id, rr.test_id)

    db.delete(rr)
    log_audit_event(
        db,
        tenant_id=tenant_context.tenant_id,
        action_code="reference_range.deleted",
        actor_user_id=actor_user_id or tenant_context.user_id,
        entity_type="test_reference_range",
        entity_id=rr.id,
        before_json={"test_id": rr.test_id, "sex": rr.sex, "context": rr.context},
    )
    db.commit()



def list_reference_ranges(
    db: Session,
    *,
    tenant_context: TenantContext,
    test_id: str,
    limit: int = 50,
    offset: int = 0,
    actor_user_id: str | None = None,
) -> tuple[list[TestReferenceRange], int]:
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    _check_permission(db, tenant_context=tenant_context, permission_code="test.view", actor_user_id=actor_user_id)

    test = _get_test_in_tenant(db, tenant_context.tenant_id, test_id)

    limit = min(max(1, limit), 100)
    offset = max(0, offset)

    query = db.query(TestReferenceRange).filter(TestReferenceRange.test_id == test.id)
    total = query.count()
    items = query.order_by(TestReferenceRange.priority.asc(), TestReferenceRange.id.asc()).offset(offset).limit(limit).all()
    return items, total


def resolve_reference_range(
    db: Session,
    *,
    tenant_context: TenantContext,
    test_id: str,
    patient_sex: str | None = None,
    patient_age_years: float | Decimal | None = None,
    patient_age_days: int | None = None,
    context: str | None = None,
    as_of: datetime | None = None,
) -> TestReferenceRange | None:
    """
    Resolve best-matching active reference range for a test based on patient attributes and clinical context.
    Matching precedence:
    1. Context match: Exact match on context > General/None context
    2. Sex match: Specific sex ('male', 'female') > 'all'
    3. Age range match: within age_min and age_max
    4. Priority: Lowest priority integer value
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    test = _get_test_in_tenant(db, tenant_context.tenant_id, test_id)

    as_of = as_of or datetime.now(timezone.utc)
    clean_sex = (patient_sex or "all").strip().lower()
    clean_context = context.strip().lower() if context else None

    age_y = Decimal(str(patient_age_years)) if patient_age_years is not None else None
    if age_y is None and patient_age_days is not None:
        age_y = Decimal(str(patient_age_days)) / Decimal("365.25")

    query = (
        db.query(TestReferenceRange)
        .filter(
            TestReferenceRange.test_id == test.id,
            TestReferenceRange.effective_from <= as_of,
            or_(TestReferenceRange.effective_to.is_(None), TestReferenceRange.effective_to >= as_of),
        )
        .order_by(TestReferenceRange.priority.asc())
    )
    ranges = query.all()
    if not ranges:
        return None

    candidate_scores: list[tuple[int, TestReferenceRange]] = []

    for r in ranges:
        if r.sex != "all" and r.sex != clean_sex:
            continue

        if clean_context and r.context and r.context != clean_context:
            continue
        if not clean_context and r.context:
            continue

        if age_y is not None:
            r_age_min = r.age_min
            r_age_max = r.age_max
            if r.age_unit == "months":
                r_age_min = (r_age_min / Decimal("12")) if r_age_min is not None else None
                r_age_max = (r_age_max / Decimal("12")) if r_age_max is not None else None
            elif r.age_unit == "days":
                r_age_min = (r_age_min / Decimal("365.25")) if r_age_min is not None else None
                r_age_max = (r_age_max / Decimal("365.25")) if r_age_max is not None else None

            if r_age_min is not None and age_y < r_age_min:
                continue
            if r_age_max is not None and age_y > r_age_max:
                continue

        score = 0
        if clean_context and r.context == clean_context:
            score += 100
        if r.sex == clean_sex and clean_sex != "all":
            score += 50
        if r.age_min is not None or r.age_max is not None:
            score += 25
        score -= r.priority

        candidate_scores.append((score, r))

    if not candidate_scores:
        for r in ranges:
            if r.sex == "all" and r.context is None and r.age_min is None and r.age_max is None:
                return r
        return None

    candidate_scores.sort(key=lambda x: x[0], reverse=True)
    return candidate_scores[0][1]



def evaluate_result_against_range(
    range_obj: TestReferenceRange | None,
    numeric_value: float | Decimal,
) -> dict[str, Any]:
    """
    Evaluate numeric result value against a reference range and produce clinical flags.
    Flags: critical_low, low, normal, high, critical_high
    """
    val = Decimal(str(numeric_value))
    if not range_obj:
        return {
            "flag": "normal",
            "is_abnormal": False,
            "is_critical": False,
            "range_text": None,
        }

    if range_obj.critical_low is not None and val < range_obj.critical_low:
        return {
            "flag": "critical_low",
            "is_abnormal": True,
            "is_critical": True,
            "low_value": float(range_obj.low_value) if range_obj.low_value is not None else None,
            "high_value": float(range_obj.high_value) if range_obj.high_value is not None else None,
            "critical_low": float(range_obj.critical_low),
            "range_text": range_obj.text_range,
        }

    if range_obj.critical_high is not None and val > range_obj.critical_high:
        return {
            "flag": "critical_high",
            "is_abnormal": True,
            "is_critical": True,
            "low_value": float(range_obj.low_value) if range_obj.low_value is not None else None,
            "high_value": float(range_obj.high_value) if range_obj.high_value is not None else None,
            "critical_high": float(range_obj.critical_high),
            "range_text": range_obj.text_range,
        }

    if range_obj.low_value is not None and val < range_obj.low_value:
        return {
            "flag": "low",
            "is_abnormal": True,
            "is_critical": False,
            "low_value": float(range_obj.low_value),
            "high_value": float(range_obj.high_value) if range_obj.high_value is not None else None,
            "range_text": range_obj.text_range,
        }

    if range_obj.high_value is not None and val > range_obj.high_value:
        return {
            "flag": "high",
            "is_abnormal": True,
            "is_critical": False,
            "low_value": float(range_obj.low_value) if range_obj.low_value is not None else None,
            "high_value": float(range_obj.high_value),
            "range_text": range_obj.text_range,
        }

    return {
        "flag": "normal",
        "is_abnormal": False,
        "is_critical": False,
        "low_value": float(range_obj.low_value) if range_obj.low_value is not None else None,
        "high_value": float(range_obj.high_value) if range_obj.high_value is not None else None,
        "range_text": range_obj.text_range,
    }


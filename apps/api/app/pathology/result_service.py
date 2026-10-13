"""Result Service: Structured Result Values, Analyte Entry, Automatic Flagging, and Clinical Audits."""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session, joinedload

from app.audit.service import log_audit_event
from app.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.identity import User
from app.models.pathology import Order, OrderItem, Result, ResultValue, Sample, Test, TestReferenceRange
from app.models.patient import Patient
from app.pathology.reference_range_service import evaluate_result_against_range, resolve_reference_range
from app.rbac.engine import authorize_action
from app.security.tenant_guard import TenantContext, verify_tenant_boundary


VALID_RESULT_STATUSES = {"draft", "entered", "verified", "released", "amended"}
PERMITTED_RESULT_TRANSITIONS = {
    "draft": {"entered"},
    "entered": {"draft", "verified"},
    "verified": {"released", "entered"},
    "released": {"amended"},
    "amended": set(),
}


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


def _try_parse_decimal(val: Any) -> Decimal | None:
    if val is None:
        return None
    s = str(val).strip()
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        # Handle formats like "< 0.05" or "> 1000" if needed
        match = re.search(r"[-+]?\d*\.?\d+", s)
        if match:
            try:
                return Decimal(match.group(0))
            except (InvalidOperation, ValueError):
                return None
        return None


def record_result_values(
    db: Session,
    *,
    tenant_context: TenantContext,
    order_item_id: str,
    values: list[dict[str, Any]],
    status: str = "draft",
    sample_id: str | None = None,
    notes: str | None = None,
    context: str | None = None,
    actor_user_id: str | None = None,
) -> Result:
    """
    Record structured analyte values against an order item with reference range matching and flag resolution.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id
    effective_user_id = actor_user_id or tenant_context.user_id

    _check_permission(db, tenant_context=tenant_context, permission_code="result.enter", actor_user_id=effective_user_id)

    order_item = (
        db.query(OrderItem)
        .join(Order, OrderItem.order_id == Order.id)
        .filter(OrderItem.id == order_item_id, Order.tenant_id == tenant_id)
        .first()
    )
    if not order_item:
        raise NotFoundError(f"Order item '{order_item_id}' not found")

    patient = db.query(Patient).filter(Patient.id == order_item.order.patient_id).first()
    if not patient:
        raise NotFoundError(f"Patient '{order_item.order.patient_id}' not found")

    clean_status = (status or "draft").strip().lower()
    if clean_status not in {"draft", "entered"}:
        raise ValidationError(f"Initial result status must be 'draft' or 'entered', got '{status}'", field="status")

    if not values:
        raise ValidationError("Result values list cannot be empty", field="values")

    # Find existing latest result for this order_item
    latest_result = (
        db.query(Result)
        .filter(Result.tenant_id == tenant_id, Result.order_item_id == order_item.id)
        .order_by(Result.version.desc())
        .first()
    )

    now = datetime.now(timezone.utc)
    if latest_result:
        if latest_result.status in {"released", "verified"}:
            raise ConflictError(
                f"Cannot directly enter results for order item in status '{latest_result.status}'. Use amend_result() with clinical reason."
            )
        elif latest_result.status in {"draft", "entered"}:
            res = latest_result
            res.values.clear()
            db.flush()
            res.status = clean_status
            res.notes = notes
            if clean_status == "entered":
                res.entered_by = effective_user_id
                res.entered_at = now
    else:
        res = Result(
            tenant_id=tenant_id,
            order_item_id=order_item.id,
            sample_id=sample_id,
            version=1,
            status=clean_status,
            notes=notes,
            entered_by=effective_user_id if clean_status == "entered" else None,
            entered_at=now if clean_status == "entered" else None,
        )
        db.add(res)
        db.flush()

    # Calculate patient age
    patient_age_years = None
    if getattr(patient, "date_of_birth", None):
        patient_age_years = (now.date() - patient.date_of_birth).days / 365.25
    elif getattr(patient, "age_years", None):
        patient_age_years = float(patient.age_years)

    for val_input in values:
        analyte_code = str(val_input.get("analyte_code", "")).strip().upper()
        if not analyte_code:
            raise ValidationError("analyte_code is required for each result value", field="analyte_code")

        raw_val = str(val_input.get("raw_value", "")).strip() if val_input.get("raw_value") is not None else None
        num_val = _try_parse_decimal(val_input.get("numeric_value") if val_input.get("numeric_value") is not None else raw_val)
        unit = val_input.get("unit") or (order_item.test.unit if order_item.test else None)

        ref_range_id = val_input.get("reference_range_id")
        ref_range = None
        if ref_range_id:
            ref_range = db.query(TestReferenceRange).filter(TestReferenceRange.id == ref_range_id).first()
        elif order_item.test_id:
            ref_range = resolve_reference_range(
                db,
                tenant_context=tenant_context,
                test_id=order_item.test_id,
                patient_sex=patient.sex,
                patient_age_years=patient_age_years,
                context=context or val_input.get("context"),
                as_of=now,
            )

        abnormal_flag = val_input.get("abnormal_flag")
        critical_flag = bool(val_input.get("critical_flag", False))
        ref_text = val_input.get("reference_text")

        if ref_range:
            ref_range_id = ref_range.id
            if not ref_text and ref_range.text_range:
                ref_text = ref_range.text_range
            elif not ref_text and (ref_range.low_value is not None or ref_range.high_value is not None):
                low_str = f"{ref_range.low_value:g}" if ref_range.low_value is not None else ""
                high_str = f"{ref_range.high_value:g}" if ref_range.high_value is not None else ""
                ref_text = f"{low_str} - {high_str} {unit or ''}".strip()

            if num_val is not None and not abnormal_flag:
                evaluation = evaluate_result_against_range(ref_range, num_val)
                abnormal_flag = evaluation["flag"]
                critical_flag = evaluation["is_critical"]

        rv = ResultValue(
            result_id=res.id,
            analyte_code=analyte_code,
            analyte_name=val_input.get("analyte_name") or order_item.test.name if order_item.test else analyte_code,
            raw_value=raw_val,
            numeric_value=num_val,
            unit=unit,
            reference_text=ref_text,
            reference_range_id=ref_range_id,
            abnormal_flag=abnormal_flag or "normal",
            critical_flag=critical_flag,
            notes=val_input.get("notes"),
        )
        db.add(rv)

    db.flush()

    log_audit_event(
        db,
        tenant_id=tenant_id,
        action_code="result.entered" if clean_status == "entered" else "result.draft_saved",
        actor_user_id=effective_user_id,
        entity_type="result",
        entity_id=res.id,
        after_json={
            "order_item_id": order_item.id,
            "version": res.version,
            "status": res.status,
            "values_count": len(values),
        },
    )

    db.commit()
    db.refresh(res)
    return res



def get_result(
    db: Session,
    *,
    tenant_context: TenantContext,
    result_id: str,
    actor_user_id: str | None = None,
) -> Result:
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    _check_permission(db, tenant_context=tenant_context, permission_code="result.view", actor_user_id=actor_user_id)

    res = (
        db.query(Result)
        .options(joinedload(Result.values), joinedload(Result.order_item))
        .filter(Result.id == result_id, Result.tenant_id == tenant_context.tenant_id)
        .first()
    )
    if not res:
        raise NotFoundError(f"Result '{result_id}' not found")
    return res


def list_results(
    db: Session,
    *,
    tenant_context: TenantContext,
    order_item_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    actor_user_id: str | None = None,
) -> tuple[list[Result], int]:
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    _check_permission(db, tenant_context=tenant_context, permission_code="result.view", actor_user_id=actor_user_id)

    limit = min(max(1, limit), 100)
    offset = max(0, offset)

    query = db.query(Result).filter(Result.tenant_id == tenant_context.tenant_id)
    if order_item_id:
        query = query.filter(Result.order_item_id == order_item_id)
    if status:
        query = query.filter(Result.status == status)

    total = query.count()
    items = query.order_by(Result.created_at.desc()).offset(offset).limit(limit).all()
    return items, total


def update_result_value(
    db: Session,
    *,
    tenant_context: TenantContext,
    result_value_id: str,
    raw_value: str,
    numeric_value: float | Decimal | None = None,
    notes: str | None = None,
    actor_user_id: str | None = None,
) -> ResultValue:
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    effective_user_id = actor_user_id or tenant_context.user_id
    _check_permission(db, tenant_context=tenant_context, permission_code="result.edit", actor_user_id=effective_user_id)

    rv = db.query(ResultValue).join(Result).filter(
        ResultValue.id == result_value_id,
        Result.tenant_id == tenant_context.tenant_id,
    ).first()
    if not rv:
        raise NotFoundError(f"Result value '{result_value_id}' not found")

    if rv.result.status in {"released", "amended"}:
        raise ConflictError(f"Cannot edit result value in status '{rv.result.status}' directly. Amendment required.")

    num_val = _try_parse_decimal(numeric_value if numeric_value is not None else raw_value)
    before_state = {"raw_value": rv.raw_value, "numeric_value": float(rv.numeric_value) if rv.numeric_value is not None else None}

    rv.raw_value = str(raw_value).strip()
    rv.numeric_value = num_val
    if notes:
        rv.notes = notes

    if rv.reference_range_id and num_val is not None:
        rr = db.query(TestReferenceRange).filter(TestReferenceRange.id == rv.reference_range_id).first()
        if rr:
            evaluation = evaluate_result_against_range(rr, num_val)
            rv.abnormal_flag = evaluation["flag"]
            rv.critical_flag = evaluation["is_critical"]

    log_audit_event(
        db,
        tenant_id=tenant_context.tenant_id,
        action_code="result_value.updated",
        actor_user_id=effective_user_id,
        entity_type="result_value",
        entity_id=rv.id,
        before_json=before_state,
        after_json={"raw_value": rv.raw_value, "numeric_value": float(rv.numeric_value) if rv.numeric_value is not None else None, "abnormal_flag": rv.abnormal_flag},
    )

    db.commit()
    db.refresh(rv)
    return rv



def verify_result(
    db: Session,
    *,
    tenant_context: TenantContext,
    result_id: str,
    notes: str | None = None,
    actor_user_id: str | None = None,
) -> Result:
    """
    Verify an entered lab result according to technician verification workflow and RBAC.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id
    effective_user_id = actor_user_id or tenant_context.user_id

    _check_permission(db, tenant_context=tenant_context, permission_code="result.verify", actor_user_id=effective_user_id)

    res = (
        db.query(Result)
        .options(joinedload(Result.values))
        .filter(Result.id == result_id, Result.tenant_id == tenant_id)
        .first()
    )
    if not res:
        raise NotFoundError(f"Result '{result_id}' not found")

    if res.status != "entered":
        raise ConflictError(f"Cannot verify result in status '{res.status}'. Result must be in 'entered' status.")

    now = datetime.now(timezone.utc)
    res.status = "verified"
    res.verified_by = effective_user_id
    res.verified_at = now
    if notes:
        res.notes = f"{res.notes}\n[Verification]: {notes}".strip() if res.notes else notes

    log_audit_event(
        db,
        tenant_id=tenant_id,
        action_code="result.verified",
        actor_user_id=effective_user_id,
        entity_type="result",
        entity_id=res.id,
        before_json={"status": "entered"},
        after_json={
            "status": "verified",
            "verified_by": effective_user_id,
            "verified_at": now.isoformat(),
            "notes": notes,
        },
    )

    db.commit()
    db.refresh(res)
    return res


def return_result_for_retest(
    db: Session,
    *,
    tenant_context: TenantContext,
    result_id: str,
    reason: str,
    actor_user_id: str | None = None,
) -> Result:
    """
    Reject verification and return result back to draft/entered status for technician re-entry.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id
    effective_user_id = actor_user_id or tenant_context.user_id

    _check_permission(db, tenant_context=tenant_context, permission_code="result.verify", actor_user_id=effective_user_id)

    clean_reason = (reason or "").strip()
    if not clean_reason:
        raise ValidationError("Reason is required when returning result for retest/re-entry", field="reason")

    res = db.query(Result).filter(Result.id == result_id, Result.tenant_id == tenant_id).first()
    if not res:
        raise NotFoundError(f"Result '{result_id}' not found")

    if res.status not in {"entered", "verified"}:
        raise ConflictError(f"Cannot return result in status '{res.status}' for re-entry")

    prev_status = res.status
    res.status = "draft"
    res.verified_by = None
    res.verified_at = None
    res.notes = f"Returned for re-entry: {clean_reason}"

    log_audit_event(
        db,
        tenant_id=tenant_id,
        action_code="result.returned_for_retest",
        actor_user_id=effective_user_id,
        entity_type="result",
        entity_id=res.id,
        before_json={"status": prev_status},
        after_json={"status": "draft", "reason": clean_reason},
    )

    db.commit()
    db.refresh(res)
    return res


def batch_verify_results(
    db: Session,
    *,
    tenant_context: TenantContext,
    result_ids: list[str],
    notes: str | None = None,
    actor_user_id: str | None = None,
) -> list[Result]:
    """
    Batch verify multiple entered results in a single transaction.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    if not result_ids:
        raise ValidationError("result_ids list cannot be empty", field="result_ids")

    verified_list = []
    for rid in result_ids:
        v = verify_result(db, tenant_context=tenant_context, result_id=rid, notes=notes, actor_user_id=actor_user_id)
        verified_list.append(v)
    return verified_list



def generate_result_signature_hash(result: Result) -> str:
    """Generate deterministic SHA256 checksum representing clinical sign-off state."""
    import hashlib
    data_parts = [
        result.id,
        result.tenant_id,
        result.order_item_id,
        str(result.version),
        result.approved_at.isoformat() if result.approved_at else "",
        result.approved_by or "",
    ]
    for rv in sorted(result.values, key=lambda v: v.analyte_code):
        data_parts.append(f"{rv.analyte_code}:{rv.raw_value}:{rv.numeric_value}:{rv.abnormal_flag}:{rv.critical_flag}")
    payload = "|".join(data_parts).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def approve_and_release_result(
    db: Session,
    *,
    tenant_context: TenantContext,
    result_id: str,
    notes: str | None = None,
    actor_user_id: str | None = None,
) -> Result:
    """
    Pathologist review, digital approval, cryptographic signature hash generation, and report release.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id
    effective_user_id = actor_user_id or tenant_context.user_id

    _check_permission(db, tenant_context=tenant_context, permission_code="result.approve", actor_user_id=effective_user_id)

    res = (
        db.query(Result)
        .options(joinedload(Result.values), joinedload(Result.order_item))
        .filter(Result.id == result_id, Result.tenant_id == tenant_id)
        .first()
    )
    if not res:
        raise NotFoundError(f"Result '{result_id}' not found")

    if res.status != "verified":
        raise ConflictError(f"Cannot approve result in status '{res.status}'. Result must be in 'verified' status.")

    now = datetime.now(timezone.utc)
    res.status = "released"
    res.approved_by = effective_user_id
    res.approved_at = now
    if notes:
        res.notes = f"{res.notes}\n[Approval]: {notes}".strip() if res.notes else notes

    sig_hash = generate_result_signature_hash(res)
    res.signature_hash = sig_hash

    # Mark OrderItem completed
    if res.order_item:
        res.order_item.status = "completed"

    log_audit_event(
        db,
        tenant_id=tenant_id,
        action_code="result.approved",
        actor_user_id=effective_user_id,
        entity_type="result",
        entity_id=res.id,
        before_json={"status": "verified"},
        after_json={
            "status": "released",
            "approved_by": effective_user_id,
            "approved_at": now.isoformat(),
            "signature_hash": sig_hash,
            "notes": notes,
        },
    )

    db.commit()
    db.refresh(res)
    return res


def reject_pathologist_approval(
    db: Session,
    *,
    tenant_context: TenantContext,
    result_id: str,
    reason: str,
    actor_user_id: str | None = None,
) -> Result:
    """
    Reject pathologist approval, returning verified result to entered status with mandatory clinical explanation.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id
    effective_user_id = actor_user_id or tenant_context.user_id

    _check_permission(db, tenant_context=tenant_context, permission_code="result.approve", actor_user_id=effective_user_id)

    clean_reason = (reason or "").strip()
    if not clean_reason:
        raise ValidationError("Clinical rejection reason is required", field="reason")

    res = db.query(Result).filter(Result.id == result_id, Result.tenant_id == tenant_id).first()
    if not res:
        raise NotFoundError(f"Result '{result_id}' not found")

    if res.status != "verified":
        raise ConflictError(f"Cannot reject approval for result in status '{res.status}'. Must be in 'verified' status.")

    res.status = "entered"
    res.verified_by = None
    res.verified_at = None
    res.notes = f"Pathologist rejected: {clean_reason}"

    log_audit_event(
        db,
        tenant_id=tenant_id,
        action_code="result.approval_rejected",
        actor_user_id=effective_user_id,
        entity_type="result",
        entity_id=res.id,
        before_json={"status": "verified"},
        after_json={"status": "entered", "reason": clean_reason},
    )

    db.commit()
    db.refresh(res)
    return res


def batch_approve_results(
    db: Session,
    *,
    tenant_context: TenantContext,
    result_ids: list[str],
    notes: str | None = None,
    actor_user_id: str | None = None,
) -> list[Result]:
    """Batch approve and release verified results."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    if not result_ids:
        raise ValidationError("result_ids list cannot be empty", field="result_ids")

    approved_list = []
    for rid in result_ids:
        app_res = approve_and_release_result(db, tenant_context=tenant_context, result_id=rid, notes=notes, actor_user_id=actor_user_id)
        approved_list.append(app_res)
    return approved_list



def amend_result(
    db: Session,
    *,
    tenant_context: TenantContext,
    result_id: str,
    amendment_reason: str,
    updated_values: list[dict[str, Any]] | None = None,
    notes: str | None = None,
    actor_user_id: str | None = None,
) -> Result:
    """
    Create a new amendment version of a released clinical result, preserving previous version immutability.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id
    effective_user_id = actor_user_id or tenant_context.user_id

    _check_permission(db, tenant_context=tenant_context, permission_code="result.edit", actor_user_id=effective_user_id)

    clean_reason = (amendment_reason or "").strip()
    if not clean_reason:
        raise ValidationError("amendment_reason is required to amend a released clinical result", field="amendment_reason")

    prior_res = (
        db.query(Result)
        .options(joinedload(Result.values))
        .filter(Result.id == result_id, Result.tenant_id == tenant_id)
        .first()
    )
    if not prior_res:
        raise NotFoundError(f"Result '{result_id}' not found")

    if prior_res.status != "released":
        raise ConflictError(f"Cannot amend result in status '{prior_res.status}'. Only 'released' results can be amended.")

    now = datetime.now(timezone.utc)
    prior_res.status = "amended"
    prior_res.amendment_reason = clean_reason
    db.flush()

    new_version_num = prior_res.version + 1
    new_res = Result(
        tenant_id=tenant_id,
        order_item_id=prior_res.order_item_id,
        sample_id=prior_res.sample_id,
        version=new_version_num,
        status="entered",
        amended_from_id=prior_res.id,
        amendment_reason=clean_reason,
        notes=notes or prior_res.notes,
        entered_by=effective_user_id,
        entered_at=now,
    )
    db.add(new_res)
    db.flush()

    values_map: dict[str, dict[str, Any]] = {}
    for old_v in prior_res.values:
        values_map[old_v.analyte_code.upper()] = {
            "analyte_code": old_v.analyte_code,
            "analyte_name": old_v.analyte_name,
            "raw_value": old_v.raw_value,
            "numeric_value": old_v.numeric_value,
            "unit": old_v.unit,
            "reference_text": old_v.reference_text,
            "reference_range_id": old_v.reference_range_id,
            "abnormal_flag": old_v.abnormal_flag,
            "critical_flag": old_v.critical_flag,
            "notes": old_v.notes,
        }

    if updated_values:
        for u in updated_values:
            code = str(u.get("analyte_code", "")).strip().upper()
            if code in values_map:
                if "raw_value" in u and "numeric_value" not in u:
                    values_map[code]["numeric_value"] = None
                values_map[code].update(u)
            else:
                values_map[code] = u

    for val_data in values_map.values():
        raw_s = str(val_data.get("raw_value", "")).strip() if val_data.get("raw_value") is not None else None
        num_v = _try_parse_decimal(val_data.get("numeric_value") if val_data.get("numeric_value") is not None else raw_s)
        new_rv = ResultValue(
            result_id=new_res.id,
            analyte_code=val_data["analyte_code"].upper(),
            analyte_name=val_data.get("analyte_name"),
            raw_value=raw_s,
            numeric_value=num_v,
            unit=val_data.get("unit"),
            reference_text=val_data.get("reference_text"),
            reference_range_id=val_data.get("reference_range_id"),
            abnormal_flag=val_data.get("abnormal_flag", "normal"),
            critical_flag=bool(val_data.get("critical_flag", False)),
            notes=val_data.get("notes"),
        )
        db.add(new_rv)

    db.flush()

    log_audit_event(
        db,
        tenant_id=tenant_id,
        action_code="result.amended",
        actor_user_id=effective_user_id,
        entity_type="result",
        entity_id=new_res.id,
        before_json={"prior_result_id": prior_res.id, "prior_version": prior_res.version, "status": "amended"},
        after_json={
            "new_result_id": new_res.id,
            "new_version": new_res.version,
            "reason": clean_reason,
            "status": new_res.status,
        },
    )

    db.commit()
    db.refresh(new_res)
    return new_res


def get_result_version_history(
    db: Session,
    *,
    tenant_context: TenantContext,
    order_item_id: str,
    actor_user_id: str | None = None,
) -> list[Result]:
    """
    Retrieve all historical versions of results for an order item in chronological version order.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    _check_permission(db, tenant_context=tenant_context, permission_code="result.view", actor_user_id=actor_user_id)

    versions = (
        db.query(Result)
        .options(joinedload(Result.values))
        .filter(
            Result.tenant_id == tenant_context.tenant_id,
            Result.order_item_id == order_item_id,
        )
        .order_by(Result.version.asc())
        .all()
    )
    return versions


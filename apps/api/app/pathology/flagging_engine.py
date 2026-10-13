"""Abnormal & Critical Flagging Engine: Clinical rules, qualitative evaluation, delta checks, and critical alert notifications."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select, and_, or_, desc
from sqlalchemy.orm import Session

from app.audit.service import log_audit_event
from app.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.identity import User
from app.models.pathology import CriticalAlert, Order, OrderItem, Result, ResultValue, TestReferenceRange
from app.pathology.reference_range_service import evaluate_result_against_range
from app.rbac.engine import authorize_action
from app.security.tenant_guard import TenantContext, verify_tenant_boundary


QUALITATIVE_NORMAL_KEYWORDS = {
    "negative",
    "non-reactive",
    "nonreactive",
    "absent",
    "nil",
    "normal",
    "clear",
    "not detected",
    "none",
}

QUALITATIVE_ABNORMAL_KEYWORDS = {
    "positive",
    "reactive",
    "detected",
    "present",
    "abnormal",
    "turbid",
    "critical",
    "heavy",
    "moderate",
}


def evaluate_qualitative_flag(raw_value: str | None) -> tuple[str, bool]:
    """
    Evaluate qualitative textual result value against standard clinical conventions.
    Returns (abnormal_flag, critical_flag).
    """
    if not raw_value:
        return "normal", False
    clean = raw_value.strip().lower()

    if clean in QUALITATIVE_NORMAL_KEYWORDS:
        return "normal", False

    for norm in QUALITATIVE_NORMAL_KEYWORDS:
        if norm in clean:
            return "normal", False

    for abn in QUALITATIVE_ABNORMAL_KEYWORDS:
        if abn in clean:
            is_critical = "critical" in clean or any(term in clean for term in ("positive", "reactive")) and any(term in clean for term in ("hiv", "hbsag", "hcv"))
            return "abnormal", is_critical

    return "normal", False


def evaluate_delta_check(
    db: Session,
    *,
    tenant_id: str,
    patient_id: str,
    analyte_code: str,
    current_numeric_value: float | Decimal,
    current_result_id: str | None = None,
    max_pct_change: float = 50.0,
    max_days: int = 60,
) -> dict[str, Any]:
    """
    Compare current numeric value with patient's most recent prior historical result for this analyte.
    Detect sudden clinical delta check threshold exceedance (e.g. rapid hemoconcentration or lab error).
    """
    clean_code = analyte_code.strip().upper()
    cur_val = Decimal(str(current_numeric_value))

    query = (
        db.query(ResultValue)
        .join(Result, ResultValue.result_id == Result.id)
        .join(OrderItem, Result.order_item_id == OrderItem.id)
        .join(Order, OrderItem.order_id == Order.id)
        .filter(
            Order.tenant_id == tenant_id,
            Order.patient_id == patient_id,
            ResultValue.analyte_code == clean_code,
            ResultValue.numeric_value.is_not(None),
            Result.status.in_(["verified", "released", "amended", "entered"]),
        )
    )
    if current_result_id:
        query = query.filter(Result.id != current_result_id)

    prev_rv = query.order_by(Result.created_at.desc()).first()
    if not prev_rv or prev_rv.numeric_value is None:
        return {"delta_flag": None, "has_prior": False}

    prev_val = Decimal(str(prev_rv.numeric_value))
    if prev_val == Decimal("0"):
        return {"delta_flag": None, "has_prior": True, "previous_value": 0.0}

    pct_diff = abs((cur_val - prev_val) / prev_val) * Decimal("100")
    is_violation = pct_diff > Decimal(str(max_pct_change))

    return {
        "delta_flag": "DELTA_ALERT" if is_violation else None,
        "has_prior": True,
        "previous_value": float(prev_val),
        "current_value": float(cur_val),
        "percent_change": float(round(pct_diff, 2)),
        "is_violation": is_violation,
    }


def trigger_critical_alerts_for_result(
    db: Session,
    *,
    tenant_context: TenantContext,
    result_id: str,
    actor_user_id: str | None = None,
) -> list[CriticalAlert]:
    """
    Scan result values for critical/panic thresholds and generate actionable CriticalAlert records.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id
    effective_user_id = actor_user_id or tenant_context.user_id

    result = db.query(Result).filter(Result.id == result_id, Result.tenant_id == tenant_id).first()
    if not result:
        raise NotFoundError(f"Result '{result_id}' not found")

    order_item = result.order_item
    order = order_item.order

    alerts_created: list[CriticalAlert] = []

    for rv in result.values:
        if rv.critical_flag or rv.abnormal_flag in {"critical_low", "critical_high"}:
            # Avoid duplicate active alerts for this result value
            existing = (
                db.query(CriticalAlert)
                .filter(
                    CriticalAlert.tenant_id == tenant_id,
                    CriticalAlert.result_value_id == rv.id,
                )
                .first()
            )
            if existing:
                continue

            alert = CriticalAlert(
                tenant_id=tenant_id,
                result_id=result.id,
                result_value_id=rv.id,
                patient_id=order.patient_id,
                order_id=order.id,
                analyte_code=rv.analyte_code,
                flag=rv.abnormal_flag or "critical",
                value=str(rv.raw_value or rv.numeric_value or ""),
                status="pending_acknowledgement",
            )
            db.add(alert)
            db.flush()

            log_audit_event(
                db,
                tenant_id=tenant_id,
                action_code="critical_alert.triggered",
                actor_user_id=effective_user_id,
                entity_type="critical_alert",
                entity_id=alert.id,
                after_json={
                    "patient_id": order.patient_id,
                    "analyte_code": rv.analyte_code,
                    "flag": alert.flag,
                    "value": alert.value,
                    "status": alert.status,
                },
            )
            alerts_created.append(alert)

    if alerts_created:
        db.commit()
        for a in alerts_created:
            db.refresh(a)

    return alerts_created


def acknowledge_critical_alert(
    db: Session,
    *,
    tenant_context: TenantContext,
    alert_id: str,
    communicated_to: str,
    notes: str | None = None,
    actor_user_id: str | None = None,
) -> CriticalAlert:
    """
    Acknowledge a critical/panic lab alert with recipient communication record and auditability.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id
    effective_user_id = actor_user_id or tenant_context.user_id

    clean_comm = (communicated_to or "").strip()
    if not clean_comm:
        raise ValidationError("communicated_to is required (e.g., attending physician name and contact)", field="communicated_to")

    alert = db.query(CriticalAlert).filter(CriticalAlert.id == alert_id, CriticalAlert.tenant_id == tenant_id).first()
    if not alert:
        raise NotFoundError(f"Critical alert '{alert_id}' not found")

    if alert.status == "acknowledged":
        raise ConflictError(f"Critical alert '{alert_id}' has already been acknowledged")

    now = datetime.now(timezone.utc)
    before_status = alert.status
    alert.status = "acknowledged"
    alert.communicated_to = clean_comm
    alert.acknowledged_by = effective_user_id
    alert.acknowledged_at = now
    if notes:
        alert.notes = notes

    log_audit_event(
        db,
        tenant_id=tenant_id,
        action_code="critical_alert.acknowledged",
        actor_user_id=effective_user_id,
        entity_type="critical_alert",
        entity_id=alert.id,
        before_json={"status": before_status},
        after_json={
            "status": "acknowledged",
            "communicated_to": clean_comm,
            "acknowledged_at": now.isoformat(),
        },
    )

    db.commit()
    db.refresh(alert)
    return alert


def list_critical_alerts(
    db: Session,
    *,
    tenant_context: TenantContext,
    status: str | None = None,
    patient_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[CriticalAlert], int]:
    """
    List critical alerts with multi-tenant isolation and bounded pagination.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    limit = min(max(1, limit), 100)
    offset = max(0, offset)

    query = db.query(CriticalAlert).filter(CriticalAlert.tenant_id == tenant_context.tenant_id)
    if status:
        query = query.filter(CriticalAlert.status == status)
    if patient_id:
        query = query.filter(CriticalAlert.patient_id == patient_id)

    total = query.count()
    items = query.order_by(CriticalAlert.created_at.desc()).offset(offset).limit(limit).all()
    return items, total


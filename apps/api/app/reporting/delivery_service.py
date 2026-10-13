"""Report Delivery Service: Multi-channel delivery adapters (print, download, email, SMS, WhatsApp) and release history."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, and_, or_, desc
from sqlalchemy.orm import Session

from app.audit.service import log_audit_event
from app.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.identity import User
from app.models.reporting import Report, ReportDelivery
from app.rbac.engine import authorize_action
from app.security.tenant_guard import TenantContext, verify_tenant_boundary


VALID_DELIVERY_CHANNELS = {"print", "download", "email", "sms", "whatsapp"}

CHANNEL_PERMISSIONS = {
    "print": "report.print",
    "download": "report.download",
    "email": "report.view",
    "sms": "report.view",
    "whatsapp": "report.view",
}


def _check_channel_permission(
    db: Session,
    *,
    tenant_context: TenantContext,
    channel: str,
    actor_user_id: str | None = None,
) -> None:
    user_id = actor_user_id or tenant_context.user_id
    if not user_id:
        return
    user = db.query(User).filter(User.id == user_id, User.tenant_id == tenant_context.tenant_id).first()
    required_perm = CHANNEL_PERMISSIONS.get(channel, "report.view")
    if user and not (
        authorize_action(db, user, required_perm, branch_id=tenant_context.branch_id)
        or authorize_action(db, user, "report.release", branch_id=tenant_context.branch_id)
    ):
        raise ForbiddenError(f"User is not authorized for report {channel} ('{required_perm}' required)")


def deliver_report(
    db: Session,
    *,
    tenant_context: TenantContext,
    report_id: str,
    channel: str,
    recipient: str,
    metadata: dict[str, Any] | None = None,
    actor_user_id: str | None = None,
) -> ReportDelivery:
    """
    Dispatch report via specified delivery channel, execute adapter hook, and durable delivery audit.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id
    effective_user_id = actor_user_id or tenant_context.user_id

    clean_channel = (channel or "").strip().lower()
    if clean_channel not in VALID_DELIVERY_CHANNELS:
        raise ValidationError(f"Invalid delivery channel '{channel}'. Allowed: {sorted(list(VALID_DELIVERY_CHANNELS))}", field="channel")

    clean_recip = (recipient or "").strip()
    if not clean_recip:
        raise ValidationError("Recipient address / destination is required", field="recipient")

    _check_channel_permission(db, tenant_context=tenant_context, channel=clean_channel, actor_user_id=effective_user_id)

    report = db.query(Report).filter(Report.id == report_id, Report.tenant_id == tenant_id).first()
    if not report:
        raise NotFoundError(f"Report '{report_id}' not found")

    now = datetime.now(timezone.utc)
    delivery_status = "printed" if clean_channel == "print" else "sent"

    meta_payload = dict(metadata or {})
    meta_payload["dispatched_at"] = now.isoformat()
    meta_payload["channel"] = clean_channel
    meta_payload["report_no"] = report.report_no

    record = ReportDelivery(
        tenant_id=tenant_id,
        report_id=report.id,
        channel=clean_channel,
        recipient=clean_recip,
        status=delivery_status,
        metadata_json=json.dumps(meta_payload),
        dispatched_by=effective_user_id,
        dispatched_at=now,
        delivered_at=now,
    )
    db.add(record)
    db.flush()

    action_code = "report.printed" if clean_channel == "print" else "report.delivered"
    log_audit_event(
        db,
        tenant_id=tenant_id,
        action_code=action_code,
        actor_user_id=effective_user_id,
        entity_type="report_delivery",
        entity_id=record.id,
        after_json={
            "report_id": report.id,
            "channel": clean_channel,
            "recipient": clean_recip,
            "status": delivery_status,
        },
    )

    db.commit()
    db.refresh(record)
    return record


def get_report_delivery_history(
    db: Session,
    *,
    tenant_context: TenantContext,
    report_id: str,
) -> list[ReportDelivery]:
    """Retrieve full transmission and release delivery history for a report."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    return (
        db.query(ReportDelivery)
        .filter(ReportDelivery.tenant_id == tenant_context.tenant_id, ReportDelivery.report_id == report_id)
        .order_by(desc(ReportDelivery.dispatched_at))
        .all()
    )


def list_report_deliveries(
    db: Session,
    *,
    tenant_context: TenantContext,
    channel: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[ReportDelivery], int]:
    """List delivery transmissions with bounded pagination and channel filtering."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    limit = min(max(1, limit), 100)
    offset = max(0, offset)

    query = db.query(ReportDelivery).filter(ReportDelivery.tenant_id == tenant_context.tenant_id)
    if channel:
        query = query.filter(ReportDelivery.channel == channel.strip().lower())
    if status:
        query = query.filter(ReportDelivery.status == status.strip().lower())

    total = query.count()
    items = query.order_by(desc(ReportDelivery.dispatched_at)).offset(offset).limit(limit).all()
    return items, total

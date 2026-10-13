"""Audit service: generic audit log writer and reader."""

from __future__ import annotations

from typing import Any
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def log_audit_event(
    db: Session,
    *,
    tenant_id: str,
    action_code: str,
    actor_user_id: str | None = None,
    branch_id: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    reason: str | None = None,
    before_json: dict[str, Any] | None = None,
    after_json: dict[str, Any] | None = None,
    correlation_id: str | None = None,
) -> AuditLog:
    """Write an audit entry within a transaction."""
    log_entry = AuditLog(
        tenant_id=tenant_id,
        action_code=action_code,
        actor_user_id=actor_user_id,
        branch_id=branch_id,
        entity_type=entity_type,
        entity_id=entity_id,
        reason=reason,
        before_json=before_json,
        after_json=after_json,
        correlation_id=correlation_id,
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry


def get_audit_logs(
    db: Session,
    *,
    tenant_id: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    action_code: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[AuditLog]:
    """Read audit logs scoped to a tenant, enforcing pagination bounds."""
    limit = min(max(1, limit), 100)  # Safe bounded query
    stmt = select(AuditLog).where(AuditLog.tenant_id == tenant_id)

    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    if action_code:
        stmt = stmt.where(AuditLog.action_code == action_code)

    stmt = stmt.order_by(desc(AuditLog.created_at)).limit(limit).offset(offset)
    return list(db.scalars(stmt).all())

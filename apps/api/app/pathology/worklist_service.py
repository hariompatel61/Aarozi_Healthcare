"""Pathology Worklist Service: Department and test-level operational queues, filters, and bounded pagination."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select, and_, or_, desc
from sqlalchemy.orm import Session, joinedload

from app.audit.service import log_audit_event
from app.errors import ForbiddenError, NotFoundError, ValidationError
from app.models.core import Department
from app.models.identity import User
from app.models.pathology import Order, OrderItem, Result, ResultValue, Sample, Test
from app.models.patient import Patient
from app.rbac.engine import authorize_action
from app.security.tenant_guard import TenantContext, verify_tenant_boundary


@dataclass
class WorklistItemDTO:
    order_item_id: str
    order_id: str
    order_no: str
    patient_id: str
    patient_no: str
    patient_name: str
    patient_sex: str | None
    test_id: str
    test_code: str
    test_name: str
    department_id: str | None
    department_name: str | None
    sample_id: str | None
    sample_barcode: str | None
    sample_status: str | None
    result_id: str | None
    result_status: str
    result_version: int | None
    has_critical_flag: bool
    ordered_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _check_worklist_permission(
    db: Session,
    *,
    tenant_context: TenantContext,
    actor_user_id: str | None = None,
) -> None:
    user_id = actor_user_id or tenant_context.user_id
    if not user_id:
        return
    user = db.query(User).filter(User.id == user_id, User.tenant_id == tenant_context.tenant_id).first()
    if user and not (
        authorize_action(db, user, "result.view", branch_id=tenant_context.branch_id)
        or authorize_action(db, user, "sample.view", branch_id=tenant_context.branch_id)
        or authorize_action(db, user, "test.view", branch_id=tenant_context.branch_id)
    ):
        raise ForbiddenError("User is not authorized to view pathology worklists")


def get_department_worklist(
    db: Session,
    *,
    tenant_context: TenantContext,
    department_id: str | None = None,
    test_id: str | None = None,
    status: str | None = None,
    branch_id: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    search: str | None = None,
    is_critical_only: bool = False,
    limit: int = 50,
    offset: int = 0,
    actor_user_id: str | None = None,
) -> tuple[list[dict[str, Any]], int]:
    """
    Query operational pathology bench worklist with filters, search, and bounded pagination.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id
    _check_worklist_permission(db, tenant_context=tenant_context, actor_user_id=actor_user_id)

    limit = min(max(1, limit), 100)
    offset = max(0, offset)

    query = (
        db.query(OrderItem, Order, Patient, Test, Department)
        .join(Order, OrderItem.order_id == Order.id)
        .join(Patient, Order.patient_id == Patient.id)
        .outerjoin(Test, OrderItem.test_id == Test.id)
        .outerjoin(Department, Test.department_id == Department.id)
        .options(
            joinedload(OrderItem.samples),
            joinedload(OrderItem.results).joinedload(Result.values),
        )
        .filter(Order.tenant_id == tenant_id)
    )

    if branch_id:
        query = query.filter(Order.branch_id == branch_id)
    elif tenant_context.branch_id:
        query = query.filter(or_(Order.branch_id.is_(None), Order.branch_id == tenant_context.branch_id))

    if department_id:
        query = query.filter(Test.department_id == department_id)

    if test_id:
        query = query.filter(OrderItem.test_id == test_id)

    if date_from:
        query = query.filter(Order.ordered_at >= date_from)
    if date_to:
        query = query.filter(Order.ordered_at <= date_to)

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Patient.first_name.ilike(s),
                Patient.last_name.ilike(s),
                Patient.patient_no.ilike(s),
                Order.order_no.ilike(s),
                Test.name.ilike(s),
                Test.code.ilike(s),
            )
        )

    query = query.filter(Order.status != "cancelled", OrderItem.status != "cancelled")
    rows = query.order_by(desc(Order.ordered_at), OrderItem.id.asc()).all()

    processed_items: list[dict[str, Any]] = []

    for item, order, pat, t, dept in rows:
        latest_sample = sorted(item.samples, key=lambda s: s.created_at, reverse=True)[0] if item.samples else None
        latest_res = sorted(item.results, key=lambda r: r.version, reverse=True)[0] if item.results else None

        res_status = latest_res.status if latest_res else "pending_entry"
        res_version = latest_res.version if latest_res else None

        has_crit = False
        if latest_res:
            has_crit = any(v.critical_flag or v.abnormal_flag in ("critical_low", "critical_high") for v in latest_res.values)

        if is_critical_only and not has_crit:
            continue

        if status:
            clean_s = status.strip().lower()
            if clean_s == "pending_entry" and res_status not in ("pending_entry", "draft"):
                continue
            elif clean_s == "pending_verification" and res_status != "entered":
                continue
            elif clean_s == "pending_approval" and res_status != "verified":
                continue
            elif clean_s in ("entered", "verified", "released", "draft") and res_status != clean_s:
                continue

        dto = WorklistItemDTO(
            order_item_id=item.id,
            order_id=order.id,
            order_no=order.order_no,
            patient_id=pat.id,
            patient_no=pat.patient_no,
            patient_name=f"{pat.first_name} {pat.last_name or ''}".strip(),
            patient_sex=pat.sex,
            test_id=t.id if t else "",
            test_code=t.code if t else (item.profile_code or "MISC"),
            test_name=t.name if t else (item.profile_name or item.description),
            department_id=dept.id if dept else None,
            department_name=dept.name if dept else None,
            sample_id=latest_sample.id if latest_sample else None,
            sample_barcode=latest_sample.barcode if latest_sample else None,
            sample_status=latest_sample.status if latest_sample else None,
            result_id=latest_res.id if latest_res else None,
            result_status=res_status,
            result_version=res_version,
            has_critical_flag=has_crit,
            ordered_at=order.ordered_at.isoformat(),
            updated_at=(latest_res.updated_at if latest_res else order.ordered_at).isoformat(),
        )
        processed_items.append(dto.to_dict())


    total_count = len(processed_items)
    paged_items = processed_items[offset : offset + limit]
    return paged_items, total_count



def get_worklist_summary(
    db: Session,
    *,
    tenant_context: TenantContext,
    branch_id: str | None = None,
    actor_user_id: str | None = None,
) -> dict[str, Any]:
    """
    Get aggregated counts for worklist dashboard tiles.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    _check_worklist_permission(db, tenant_context=tenant_context, actor_user_id=actor_user_id)

    items, _ = get_department_worklist(
        db,
        tenant_context=tenant_context,
        branch_id=branch_id,
        limit=100,
        offset=0,
    )

    pending_entry = sum(1 for it in items if it["result_status"] in ("pending_entry", "draft"))
    pending_verification = sum(1 for it in items if it["result_status"] == "entered")
    pending_approval = sum(1 for it in items if it["result_status"] == "verified")
    critical_alerts = sum(1 for it in items if it["has_critical_flag"])

    return {
        "total_queued": len(items),
        "pending_entry": pending_entry,
        "pending_verification": pending_verification,
        "pending_approval": pending_approval,
        "critical_pending": critical_alerts,
    }


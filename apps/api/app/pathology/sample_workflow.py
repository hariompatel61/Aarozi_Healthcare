"""Sample workflow service: specimen collection, barcodes, receipt, acceptance, rejection, and state machine."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.audit.service import log_audit_event
from app.models.pathology import Order, OrderItem, Sample, Test
from app.pathology.order_workflow import _recalculate_order_status_from_items
from app.security.tenant_guard import TenantContext, verify_tenant_boundary


class SampleWorkflowError(Exception):
    """Base exception for sample workflow operations."""
    pass


class SampleNotFoundError(SampleWorkflowError):
    pass


class SampleStateTransitionError(SampleWorkflowError):
    pass


class InvalidSampleInputError(SampleWorkflowError):
    pass


# Valid sample state transitions:
# ORDERED -> COLLECTED -> BARCODED -> RECEIVED -> ACCEPTED -> IN_PROCESS -> RESULT_READY
# RECEIVED -> REJECTED (reason required)
VALID_SAMPLE_TRANSITIONS: dict[str, set[str]] = {
    "ordered": {"collected"},
    "collected": {"barcoded"},
    "barcoded": {"received"},
    "received": {"accepted", "rejected"},
    "accepted": {"in_process"},
    "in_process": {"result_ready"},
    "result_ready": set(),
    "rejected": set(),
}


def generate_sample_barcode(db: Session, tenant_id: str, prefix: str = "SMP") -> str:
    """
    Generate unique, tenant-scoped sample barcode format: SMP-YYYYMMDD-XXXX.
    Guaranteed unique per tenant.
    """
    today_str = datetime.utcnow().strftime("%Y%m%d")
    match_pattern = f"{prefix}-{today_str}-%"

    count = (
        db.query(func.count(Sample.id))
        .filter(Sample.tenant_id == tenant_id, Sample.barcode.like(match_pattern))
        .scalar()
        or 0
    )
    return f"{prefix}-{today_str}-{count + 1:04d}"


def create_sample_for_order_item(
    db: Session,
    *,
    tenant_context: TenantContext,
    order_item_id: str,
    barcode: str | None = None,
    specimen_type: str | None = None,
    container_type: str | None = None,
    initial_status: str = "ordered",
) -> Sample:
    """
    Create an initial sample record linked to an OrderItem.
    If specimen_type or container_type are omitted, fallback to Test definitions.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id

    # Verify order item exists in tenant
    stmt = (
        select(OrderItem)
        .join(Order, Order.id == OrderItem.order_id)
        .options(selectinload(OrderItem.test), selectinload(OrderItem.order))
        .where(Order.tenant_id == tenant_id, OrderItem.id == order_item_id)
    )
    order_item = db.scalars(stmt).first()
    if not order_item:
        raise InvalidSampleInputError(f"OrderItem '{order_item_id}' not found in tenant.")

    assigned_barcode = barcode or generate_sample_barcode(db, tenant_id)

    # Check barcode uniqueness in tenant
    existing = (
        db.query(Sample.id)
        .filter(Sample.tenant_id == tenant_id, Sample.barcode == assigned_barcode)
        .first()
    )
    if existing:
        raise InvalidSampleInputError(f"Barcode '{assigned_barcode}' already exists for tenant.")

    test = order_item.test
    effective_specimen = specimen_type or (test.specimen_type if test else None)
    effective_container = container_type or (test.container_type if test else None)

    sample = Sample(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        order_item_id=order_item.id,
        barcode=assigned_barcode,
        specimen_type=effective_specimen,
        container_type=effective_container,
        status=initial_status,
    )
    db.add(sample)
    db.flush()
    return sample


def collect_sample(
    db: Session,
    *,
    tenant_context: TenantContext,
    sample_id: str,
    collected_by: str | None = None,
    collected_at: datetime | None = None,
) -> Sample:
    """
    Mark sample as collected (ORDERED -> COLLECTED).
    Updates OrderItem and parent Order status to 'sample_collected' if appropriate.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    sample = get_sample(db, tenant_context=tenant_context, sample_id=sample_id)

    if sample.status != "ordered":
        raise SampleStateTransitionError(
            f"Cannot collect sample in status '{sample.status}'. Expected 'ordered'."
        )

    actor = collected_by or tenant_context.user_id
    sample.status = "collected"
    sample.collected_at = collected_at or datetime.utcnow()
    sample.collected_by = actor

    # Update order item and parent order
    order_item = sample.order_item
    if order_item and order_item.status in {"draft", "placed"}:
        order_item.status = "sample_collected"
        if order_item.order and order_item.order.status in {"draft", "placed"}:
            order_item.order.status = "sample_collected"

    log_audit_event(
        db,
        tenant_id=tenant_context.tenant_id,
        action_code="sample.collect",
        actor_user_id=actor,
        branch_id=tenant_context.branch_id,
        entity_type="sample",
        entity_id=sample.id,
        after_json={"status": "collected", "barcode": sample.barcode},
    )

    db.flush()
    return sample


def barcode_sample(
    db: Session,
    *,
    tenant_context: TenantContext,
    sample_id: str,
    barcode: str | None = None,
) -> Sample:
    """
    Barcode sample (COLLECTED -> BARCODED).
    Can update the barcode label or finalize assignment.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    sample = get_sample(db, tenant_context=tenant_context, sample_id=sample_id)

    if sample.status != "collected":
        raise SampleStateTransitionError(
            f"Cannot barcode sample in status '{sample.status}'. Expected 'collected'."
        )

    if barcode and barcode != sample.barcode:
        existing = (
            db.query(Sample.id)
            .filter(Sample.tenant_id == tenant_context.tenant_id, Sample.barcode == barcode)
            .first()
        )
        if existing:
            raise InvalidSampleInputError(f"Barcode '{barcode}' already exists for tenant.")
        sample.barcode = barcode

    sample.status = "barcoded"

    log_audit_event(
        db,
        tenant_id=tenant_context.tenant_id,
        action_code="sample.barcode",
        actor_user_id=tenant_context.user_id,
        branch_id=tenant_context.branch_id,
        entity_type="sample",
        entity_id=sample.id,
        after_json={"status": "barcoded", "barcode": sample.barcode},
    )

    db.flush()
    return sample


def receive_sample(
    db: Session,
    *,
    tenant_context: TenantContext,
    sample_id: str,
    received_by: str | None = None,
    received_at: datetime | None = None,
) -> Sample:
    """
    Receive sample at laboratory accessioning (BARCODED -> RECEIVED).
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    sample = get_sample(db, tenant_context=tenant_context, sample_id=sample_id)

    if sample.status != "barcoded":
        raise SampleStateTransitionError(
            f"Cannot receive sample in status '{sample.status}'. Expected 'barcoded'."
        )

    actor = received_by or tenant_context.user_id
    sample.status = "received"
    sample.received_at = received_at or datetime.utcnow()
    sample.received_by = actor

    log_audit_event(
        db,
        tenant_id=tenant_context.tenant_id,
        action_code="sample.receive",
        actor_user_id=actor,
        branch_id=tenant_context.branch_id,
        entity_type="sample",
        entity_id=sample.id,
        after_json={"status": "received", "barcode": sample.barcode},
    )

    db.flush()
    return sample


def accept_sample(
    db: Session,
    *,
    tenant_context: TenantContext,
    sample_id: str,
    accepted_by: str | None = None,
    accepted_at: datetime | None = None,
) -> Sample:
    """
    Accept sample into processing (RECEIVED -> ACCEPTED).
    OrderItem status advances to in_process.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    sample = get_sample(db, tenant_context=tenant_context, sample_id=sample_id)

    if sample.status != "received":
        raise SampleStateTransitionError(
            f"Cannot accept sample in status '{sample.status}'. Expected 'received'."
        )

    actor = accepted_by or tenant_context.user_id
    sample.status = "accepted"
    sample.accepted_at = accepted_at or datetime.utcnow()
    sample.accepted_by = actor

    order_item = sample.order_item
    if order_item:
        order_item.status = "in_process"
        if order_item.order and order_item.order.status in {"draft", "placed", "sample_collected"}:
            order_item.order.status = "in_process"

    log_audit_event(
        db,
        tenant_id=tenant_context.tenant_id,
        action_code="sample.accept",
        actor_user_id=actor,
        branch_id=tenant_context.branch_id,
        entity_type="sample",
        entity_id=sample.id,
        after_json={"status": "accepted", "barcode": sample.barcode},
    )

    db.flush()
    return sample


def reject_sample(
    db: Session,
    *,
    tenant_context: TenantContext,
    sample_id: str,
    reason: str,
    rejected_by: str | None = None,
    rejected_at: datetime | None = None,
) -> Sample:
    """
    Reject sample at accessioning (RECEIVED -> REJECTED).
    Reason is strictly required per state machines.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    if not reason or not reason.strip():
        raise SampleStateTransitionError("Rejection reason is mandatory when rejecting a sample.")

    sample = get_sample(db, tenant_context=tenant_context, sample_id=sample_id)

    if sample.status != "received":
        raise SampleStateTransitionError(
            f"Cannot reject sample in status '{sample.status}'. Expected 'received'."
        )

    actor = rejected_by or tenant_context.user_id
    sample.status = "rejected"
    sample.rejected_at = rejected_at or datetime.utcnow()
    sample.rejected_by = actor
    sample.rejection_reason = reason.strip()

    log_audit_event(
        db,
        tenant_id=tenant_context.tenant_id,
        action_code="sample.reject",
        actor_user_id=actor,
        branch_id=tenant_context.branch_id,
        entity_type="sample",
        entity_id=sample.id,
        reason=reason.strip(),
        after_json={"status": "rejected", "reason": reason.strip()},
    )

    db.flush()
    return sample


def advance_sample_status(
    db: Session,
    *,
    tenant_context: TenantContext,
    sample_id: str,
    target_status: str,
    reason: str | None = None,
    actor_id: str | None = None,
) -> Sample:
    """
    Generic transition helper enforcing the sample state machine:
    ORDERED -> COLLECTED -> BARCODED -> RECEIVED -> ACCEPTED -> IN_PROCESS -> RESULT_READY
    RECEIVED -> REJECTED (reason required)
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    sample = get_sample(db, tenant_context=tenant_context, sample_id=sample_id)
    current = sample.status

    if current == target_status:
        return sample

    allowed = VALID_SAMPLE_TRANSITIONS.get(current, set())
    if target_status not in allowed:
        raise SampleStateTransitionError(
            f"Cannot transition sample from '{current}' to '{target_status}'. Allowed: {sorted(list(allowed))}"
        )

    if target_status == "collected":
        return collect_sample(db, tenant_context=tenant_context, sample_id=sample_id, collected_by=actor_id)
    elif target_status == "barcoded":
        return barcode_sample(db, tenant_context=tenant_context, sample_id=sample_id)
    elif target_status == "received":
        return receive_sample(db, tenant_context=tenant_context, sample_id=sample_id, received_by=actor_id)
    elif target_status == "accepted":
        return accept_sample(db, tenant_context=tenant_context, sample_id=sample_id, accepted_by=actor_id)
    elif target_status == "rejected":
        if not reason:
            raise SampleStateTransitionError("Rejection reason is mandatory when rejecting a sample.")
        return reject_sample(db, tenant_context=tenant_context, sample_id=sample_id, reason=reason, rejected_by=actor_id)
    elif target_status == "in_process":
        sample.status = "in_process"
        if sample.order_item:
            sample.order_item.status = "in_process"
        db.flush()
        return sample
    elif target_status == "result_ready":
        sample.status = "result_ready"
        db.flush()
        return sample
    else:
        raise SampleStateTransitionError(f"Unsupported target status '{target_status}'.")


def get_sample(
    db: Session,
    *,
    tenant_context: TenantContext,
    sample_id: str,
) -> Sample:
    """Get sample by ID ensuring tenant boundaries."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    stmt = (
        select(Sample)
        .options(
            selectinload(Sample.order_item).selectinload(OrderItem.order),
            selectinload(Sample.order_item).selectinload(OrderItem.test),
        )
        .where(Sample.tenant_id == tenant_context.tenant_id, Sample.id == sample_id)
    )
    sample = db.scalars(stmt).first()
    if not sample:
        raise SampleNotFoundError(f"Sample '{sample_id}' not found in tenant.")
    return sample


def get_sample_by_barcode(
    db: Session,
    *,
    tenant_context: TenantContext,
    barcode: str,
) -> Sample:
    """Look up sample by barcode ensuring tenant boundaries."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    stmt = (
        select(Sample)
        .options(
            selectinload(Sample.order_item).selectinload(OrderItem.order),
            selectinload(Sample.order_item).selectinload(OrderItem.test),
        )
        .where(Sample.tenant_id == tenant_context.tenant_id, Sample.barcode == barcode)
    )
    sample = db.scalars(stmt).first()
    if not sample:
        raise SampleNotFoundError(f"Sample with barcode '{barcode}' not found in tenant.")
    return sample


def list_samples(
    db: Session,
    *,
    tenant_context: TenantContext,
    status: str | None = None,
    order_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Sample]:
    """List samples for a tenant with bounded pagination."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    clamped_limit = max(1, min(limit, 100))

    query = (
        select(Sample)
        .options(
            selectinload(Sample.order_item).selectinload(OrderItem.test),
        )
        .where(Sample.tenant_id == tenant_context.tenant_id)
    )
    if status:
        query = query.where(Sample.status == status)
    if order_id:
        query = query.join(OrderItem, OrderItem.id == Sample.order_item_id).where(OrderItem.order_id == order_id)

    query = query.order_by(Sample.created_at.desc()).offset(offset).limit(clamped_limit)
    return list(db.scalars(query).all())

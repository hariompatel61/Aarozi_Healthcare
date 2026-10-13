"""Refund & Cancellation service: multi-tenant, auditable, permission-gated refund processing."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.audit.service import log_audit_event
from app.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.billing import Invoice, Payment, Refund
from app.models.identity import User
from app.rbac.engine import authorize_action
from app.security.tenant_guard import TenantContext, verify_tenant_boundary

VALID_REFUND_METHODS = {
    "cash",
    "card",
    "upi",
    "bank_transfer",
    "original_payment",
}


def _round_curr(val: float | Decimal) -> Decimal:
    """Helper to enforce standard 2-decimal financial rounding."""
    return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def generate_refund_no(db: Session, tenant_id: str, prefix: str = "REF") -> str:
    """
    Generate sequential, daily-scoped refund numbers per tenant.
    Format: REF-YYYYMMDD-XXXX
    """
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    like_pattern = f"{prefix}-{date_str}-%"

    count_stmt = (
        select(func.count())
        .select_from(Refund)
        .where(
            Refund.tenant_id == tenant_id,
            Refund.refund_no.like(like_pattern),
        )
    )
    existing_count = db.execute(count_stmt).scalar_one()
    seq = existing_count + 1
    return f"{prefix}-{date_str}-{seq:04d}"



def process_refund(
    db: Session,
    *,
    tenant_context: TenantContext,
    invoice_id: str,
    amount: float | Decimal,
    reason: str,
    method: str = "original_payment",
    payment_id: str | None = None,
    provider_reference: str | None = None,
    idempotency_key: str | None = None,
    actor_user_id: str | None = None,
) -> Refund:
    """
    Process a controlled financial refund against an invoice.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id

    # Check idempotency
    if idempotency_key and idempotency_key.strip():
        existing = (
            db.query(Refund)
            .filter(Refund.tenant_id == tenant_id, Refund.idempotency_key == idempotency_key.strip())
            .first()
        )
        if existing:
            return existing

    # Reason is mandatory
    clean_reason = (reason or "").strip()
    if not clean_reason:
        raise ValidationError("Refund reason is required", field="reason")

    # Validate method
    clean_method = (method or "").strip().lower()
    if clean_method not in VALID_REFUND_METHODS:
        raise ValidationError(
            f"Invalid refund method '{method}'. Allowed: {sorted(list(VALID_REFUND_METHODS))}",
            field="method",
        )

    # Validate amount
    refund_amt = _round_curr(amount)
    if refund_amt <= Decimal("0.00"):
        raise ValidationError("Refund amount must be greater than 0", field="amount")

    # Fetch invoice
    invoice = (
        db.query(Invoice)
        .filter(Invoice.id == invoice_id, Invoice.tenant_id == tenant_id)
        .first()
    )
    if not invoice:
        raise NotFoundError(f"Invoice '{invoice_id}' not found")

    # Authorize user
    effective_user_id = actor_user_id or tenant_context.user_id
    if effective_user_id:
        auth_user = (
            db.query(User)
            .filter(User.id == effective_user_id, User.tenant_id == tenant_id)
            .first()
        )
        if auth_user:
            if not authorize_action(db, auth_user, "billing.refund", branch_id=invoice.branch_id):
                raise ForbiddenError("User is not authorized to issue refunds ('billing.refund' required)")

    # Status check
    if invoice.status in {"cancelled"}:
        raise ConflictError("Cannot refund a cancelled invoice")

    # Calculate total successfully collected payments minus already processed refunds
    total_paid_stmt = (
        select(func.coalesce(func.sum(Payment.amount), 0.0))
        .where(
            Payment.tenant_id == tenant_id,
            Payment.invoice_id == invoice.id,
            Payment.status == "success",
        )
    )
    total_collected = _round_curr(db.execute(total_paid_stmt).scalar_one())

    current_refunded = _round_curr(invoice.refund_total)
    refundable_balance = total_collected - current_refunded

    if refundable_balance <= Decimal("0.00"):
        raise ConflictError("Invoice has no refundable balance")

    if refund_amt > refundable_balance:
        raise ValidationError(
            f"Refund amount ({refund_amt}) exceeds available refundable balance ({refundable_balance})",
            field="amount",
        )

    # Validate payment_id if provided
    if payment_id:
        payment = (
            db.query(Payment)
            .filter(Payment.id == payment_id, Payment.invoice_id == invoice.id, Payment.tenant_id == tenant_id)
            .first()
        )
        if not payment:
            raise NotFoundError(f"Payment '{payment_id}' not found for invoice '{invoice_id}'")

    # Generate refund number
    refund_no = generate_refund_no(db, tenant_id)

    # Create refund record
    refund = Refund(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        invoice_id=invoice.id,
        payment_id=payment_id,
        refund_no=refund_no,
        amount=float(refund_amt),
        reason=clean_reason,
        method=clean_method,
        status="completed",
        provider_reference=provider_reference.strip() if provider_reference else None,
        idempotency_key=idempotency_key.strip() if idempotency_key else None,
        processed_by=effective_user_id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(refund)

    # Update invoice refund total & paid amount & state
    prev_status = invoice.status
    new_refund_total = current_refunded + refund_amt
    invoice.refund_total = float(new_refund_total)
    
    # Net paid amount after refunds
    net_paid = total_collected - new_refund_total
    invoice.paid_amount = float(net_paid)

    # Determine status transition according to state machine
    grand_total = _round_curr(invoice.grand_total)
    if net_paid <= Decimal("0.00") and new_refund_total >= total_collected:
        invoice.status = "refunded"
    elif net_paid > Decimal("0.00") and net_paid < grand_total:
        invoice.status = "part_paid"

    # Audit event
    log_audit_event(
        db,
        tenant_id=tenant_id,
        actor_user_id=effective_user_id,
        action_code="invoice.refunded",
        entity_type="refund",
        entity_id=refund.id,
        branch_id=invoice.branch_id,
        before_json={
            "invoice_id": invoice.id,
            "status": prev_status,
            "paid_amount": float(total_collected - current_refunded),
            "refund_total": float(current_refunded),
        },
        after_json={
            "refund_id": refund.id,
            "refund_no": refund.refund_no,
            "amount": float(refund_amt),
            "reason": clean_reason,
            "method": clean_method,
            "new_status": invoice.status,
            "new_paid_amount": float(net_paid),
            "new_refund_total": float(new_refund_total),
        },
    )

    db.commit()
    db.refresh(refund)
    return refund


def get_refund(
    db: Session,
    *,
    tenant_context: TenantContext,
    refund_id: str,
) -> Refund:
    """Fetch refund by ID verifying tenant scoping."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    refund = (
        db.query(Refund)
        .options(joinedload(Refund.invoice), joinedload(Refund.payment))
        .filter(Refund.id == refund_id, Refund.tenant_id == tenant_context.tenant_id)
        .first()
    )
    if not refund:
        raise NotFoundError(f"Refund '{refund_id}' not found")
    return refund


def list_refunds(
    db: Session,
    *,
    tenant_context: TenantContext,
    invoice_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Refund], int]:
    """List refunds with tenant scoping and bounded pagination."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id

    clamped_limit = max(1, min(limit, 100))
    clamped_offset = max(0, offset)

    query = select(Refund).where(Refund.tenant_id == tenant_id)
    if invoice_id:
        query = query.where(Refund.invoice_id == invoice_id)

    count_query = select(func.count()).select_from(query.subquery())
    total_count = db.execute(count_query).scalar_one()

    stmt = (
        query.order_by(Refund.created_at.desc())
        .offset(clamped_offset)
        .limit(clamped_limit)
    )
    refunds = db.execute(stmt).scalars().all()
    return list(refunds), total_count


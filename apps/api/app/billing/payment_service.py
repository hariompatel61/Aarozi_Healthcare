"""Payment management service: payment collection, receipt generation, idempotent callbacks, and invoice settlement."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session

from app.audit.service import log_audit_event
from app.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.billing import Invoice, Payment
from app.models.identity import User
from app.models.patient import Patient
from app.rbac.engine import authorize_action
from app.security.tenant_guard import TenantContext, verify_tenant_boundary


VALID_PAYMENT_METHODS = {
    "cash",
    "card",
    "upi",
    "bank_transfer",
    "cheque",
    "online",
}


def _round_curr(val: Decimal | float | int) -> Decimal:
    return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def generate_receipt_no(db: Session, tenant_id: str, prefix: str = "RCP") -> str:
    """Generate a sequential, tenant-scoped receipt number (e.g., RCP-20261013-0001)."""
    today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    seq_pattern = f"{prefix}-{today_str}-%"

    count_today = (
        db.query(func.count(Payment.id))
        .filter(Payment.tenant_id == tenant_id, Payment.receipt_no.like(seq_pattern))
        .scalar()
        or 0
    )
    return f"{prefix}-{today_str}-{count_today + 1:04d}"



def record_payment(
    db: Session,
    *,
    tenant_context: TenantContext,
    invoice_id: str,
    amount: float,
    method: str,
    provider_reference: str | None = None,
    idempotency_key: str | None = None,
    notes: str | None = None,
    received_at: datetime | None = None,
    actor_user_id: str | None = None,
    authorizer_user: User | None = None,
) -> Payment:
    """
    Record payment against an invoice with validation, idempotency, receipt creation,
    invoice balance update, and audit logging.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id

    # RBAC authorization check (billing.payment)
    actor_id = actor_user_id or tenant_context.user_id
    auth_user = authorizer_user
    if not auth_user and actor_id:
        auth_user = db.query(User).filter(User.id == actor_id, User.tenant_id == tenant_id).first()

    if auth_user:
        if not (
            authorize_action(db, auth_user, "billing.payment")
            or authorize_action(db, auth_user, "billing.create")
        ):
            raise ForbiddenError("User is not authorized to collect payments ('billing.payment' required)")

    # Idempotency check: if already processed for this tenant, return existing record
    if idempotency_key:
        clean_key = idempotency_key.strip()
        existing = (
            db.query(Payment)
            .filter(Payment.tenant_id == tenant_id, Payment.idempotency_key == clean_key)
            .first()
        )
        if existing:
            return existing

    # Validate payment method
    clean_method = (method or "").strip().lower()
    if clean_method not in VALID_PAYMENT_METHODS:
        raise ValidationError(
            f"Invalid payment method '{method}'. Allowed: {sorted(list(VALID_PAYMENT_METHODS))}",
            field="method",
        )

    # Validate amount
    amt = _round_curr(amount)
    if amt <= Decimal("0.00"):
        raise ValidationError("Payment amount must be greater than 0", field="amount")

    # Fetch and lock invoice
    invoice = (
        db.query(Invoice)
        .filter(Invoice.id == invoice_id, Invoice.tenant_id == tenant_id)
        .first()
    )
    if not invoice:
        raise NotFoundError(f"Invoice '{invoice_id}' not found")

    # Status check
    if invoice.status in {"cancelled", "refunded"}:
        raise ConflictError(f"Cannot record payment for invoice in status '{invoice.status}'")

    grand_total = _round_curr(invoice.grand_total)
    current_paid = _round_curr(invoice.paid_amount)
    balance_due = grand_total - current_paid

    if amt > balance_due:
        raise ValidationError(
            f"Payment amount ({amt}) exceeds balance due ({balance_due})",
            field="amount",
        )

    # Generate receipt number
    receipt_no = generate_receipt_no(db, tenant_id)

    # Create payment record
    payment = Payment(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        invoice_id=invoice.id,
        amount=float(amt),
        method=clean_method,
        provider_reference=provider_reference.strip() if provider_reference else None,
        receipt_no=receipt_no,
        idempotency_key=idempotency_key.strip() if idempotency_key else None,
        status="success",
        notes=notes.strip() if notes else None,
        received_at=received_at or datetime.now(timezone.utc),
    )
    db.add(payment)

    # Update invoice paid amount and status
    new_paid = current_paid + amt
    invoice.paid_amount = float(new_paid)

    if new_paid >= grand_total:
        invoice.status = "paid"
    else:
        invoice.status = "part_paid"

    db.flush()

    # Emit payment.received audit log
    log_audit_event(
        db,
        tenant_id=tenant_id,
        actor_user_id=actor_id,
        action_code="payment.received",
        entity_type="payment",
        entity_id=payment.id,
        branch_id=invoice.branch_id,
        after_json={
            "payment_id": payment.id,
            "invoice_id": invoice.id,
            "invoice_no": invoice.invoice_no,
            "receipt_no": payment.receipt_no,
            "amount": float(payment.amount),
            "method": payment.method,
            "provider_reference": payment.provider_reference,
            "invoice_grand_total": float(invoice.grand_total),
            "invoice_paid_amount": float(invoice.paid_amount),
            "invoice_status": invoice.status,
            "balance_remaining": float(grand_total - new_paid),
        },
    )
    db.commit()
    db.refresh(payment)
    return payment



def process_payment_callback(
    db: Session,
    *,
    tenant_context: TenantContext,
    invoice_id: str,
    amount: float,
    provider: str,
    provider_reference: str,
    idempotency_key: str,
    callback_payload: dict[str, Any] | None = None,
) -> Payment:
    """
    Process asynchronous or web-based payment callback / gateway notification idempotently.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id

    if not idempotency_key or not idempotency_key.strip():
        raise ValidationError("idempotency_key is required for payment callbacks", field="idempotency_key")

    clean_key = idempotency_key.strip()
    existing = (
        db.query(Payment)
        .filter(Payment.tenant_id == tenant_id, Payment.idempotency_key == clean_key)
        .first()
    )
    if existing:
        return existing

    # Record payment under online/gateway method
    payment = record_payment(
        db,
        tenant_context=tenant_context,
        invoice_id=invoice_id,
        amount=amount,
        method="online",
        provider_reference=f"{provider}:{provider_reference}",
        idempotency_key=clean_key,
        notes=f"Callback received from {provider}",
    )
    return payment


def generate_receipt(
    db: Session,
    *,
    tenant_context: TenantContext,
    payment_id: str,
) -> dict[str, Any]:
    """
    Generate structured receipt snapshot data for printing, display, or export.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id

    payment = (
        db.query(Payment)
        .filter(Payment.id == payment_id, Payment.tenant_id == tenant_id)
        .first()
    )
    if not payment:
        raise NotFoundError(f"Payment '{payment_id}' not found")

    invoice = (
        db.query(Invoice)
        .filter(Invoice.id == payment.invoice_id, Invoice.tenant_id == tenant_id)
        .first()
    )
    if not invoice:
        raise NotFoundError(f"Invoice '{payment.invoice_id}' not found")

    patient = (
        db.query(Patient)
        .filter(Patient.id == invoice.patient_id, Patient.tenant_id == tenant_id)
        .first()
    )

    grand_total = _round_curr(invoice.grand_total)
    paid_total = _round_curr(invoice.paid_amount)
    balance_due = grand_total - paid_total

    return {
        "receipt_no": payment.receipt_no,
        "payment_id": payment.id,
        "received_at": payment.received_at.isoformat() if payment.received_at else None,
        "payment_amount": float(payment.amount),
        "payment_method": payment.method,
        "provider_reference": payment.provider_reference,
        "invoice_id": invoice.id,
        "invoice_no": invoice.invoice_no,
        "invoice_currency": invoice.currency,
        "invoice_grand_total": float(invoice.grand_total),
        "invoice_paid_amount": float(invoice.paid_amount),
        "invoice_balance_due": float(balance_due),
        "invoice_status": invoice.status,
        "patient": {
            "id": patient.id if patient else invoice.patient_id,
            "patient_no": patient.patient_no if patient else None,
            "full_name": patient.full_name if patient else "Unknown",
            "mobile": patient.mobile_normalized if patient else None,
        },
    }


def get_payment(
    db: Session,
    *,
    tenant_context: TenantContext,
    payment_id: str,
) -> Payment:
    """Fetch payment by ID ensuring multi-tenant isolation."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    pmt = (
        db.query(Payment)
        .filter(Payment.id == payment_id, Payment.tenant_id == tenant_context.tenant_id)
        .first()
    )
    if not pmt:
        raise NotFoundError(f"Payment '{payment_id}' not found")
    return pmt


def list_payments(
    db: Session,
    *,
    tenant_context: TenantContext,
    invoice_id: str | None = None,
    method: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Payment], int]:
    """List payments with tenant scoping and bounded pagination."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id

    clamped_limit = max(1, min(limit, 100))
    clamped_offset = max(0, offset)

    query = select(Payment).where(Payment.tenant_id == tenant_id)
    if invoice_id:
        query = query.where(Payment.invoice_id == invoice_id)
    if method:
        query = query.where(Payment.method == method.strip().lower())

    count_query = select(func.count()).select_from(query.subquery())
    total_count = db.execute(count_query).scalar_one()

    stmt = (
        query.order_by(desc(Payment.received_at))
        .offset(clamped_offset)
        .limit(clamped_limit)
    )
    payments = db.execute(stmt).scalars().all()
    return list(payments), total_count


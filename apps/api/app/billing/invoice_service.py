"""Invoice Engine service: generation, line-level calculations, pricing lookup, state transitions, and auditability."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.audit.service import log_audit_event
from app.billing.discount_service import calculate_line_discount
from app.billing.pricing_service import resolve_pricing_rate
from app.rbac.engine import authorize_action
from app.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.billing import Invoice, InvoiceItem, ReferralPartner
from app.models.identity import User
from app.models.pathology import Order, OrderItem
from app.models.patient import Patient
from app.security.tenant_guard import TenantContext, verify_tenant_boundary


class InvoiceNotFoundError(NotFoundError):
    """Raised when an invoice cannot be found."""
    pass


class InvoiceStateTransitionError(ValidationError):
    """Raised when an illegal invoice status transition is attempted."""
    pass


VALID_INVOICE_STATUSES = {
    "draft",
    "issued",
    "part_paid",
    "paid",
    "cancelled",
    "refund_pending",
    "refunded",
}

# Permitted state transitions according to canonical domain rules
PERMITTED_INVOICE_TRANSITIONS = {
    "draft": {"issued", "cancelled"},
    "issued": {"part_paid", "paid", "cancelled"},
    "part_paid": {"paid", "cancelled"},
    "paid": {"refund_pending"},
    "refund_pending": {"refunded", "paid"},
    "refunded": set(),
    "cancelled": set(),
}


def _round_currency(val: float | Decimal) -> float:
    """Helper to round financial decimals to 2 decimal places using half-up."""
    d = Decimal(str(val))
    return float(d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def generate_invoice_no(db: Session, tenant_id: str, prefix: str = "INV") -> str:
    """Generate a sequential, tenant-scoped invoice number (e.g., INV-20261013-0001)."""
    today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    match_pattern = f"{prefix}-{today_str}-%"

    count = (
        db.query(func.count(Invoice.id))
        .filter(Invoice.tenant_id == tenant_id, Invoice.invoice_no.like(match_pattern))
        .scalar()
        or 0
    )
    return f"{prefix}-{today_str}-{count + 1:04d}"



def create_invoice(
    db: Session,
    *,
    tenant_context: TenantContext,
    patient_id: str,
    branch_id: str | None = None,
    order_id: str | None = None,
    referral_partner_id: str | None = None,
    items: list[dict[str, Any]] | None = None,
    currency: str = "USD",
    status: str = "issued",
    notes: str | None = None,
    actor_user_id: str | None = None,
) -> Invoice:
    """
    Create an invoice with line-level auditability.
    Items can be supplied explicitly or populated automatically from an associated lab Order.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id

    # 1. Verify Patient exists and belongs to the tenant
    patient = (
        db.query(Patient)
        .filter(Patient.id == patient_id, Patient.tenant_id == tenant_id)
        .first()
    )
    if not patient:
        raise NotFoundError(f"Patient '{patient_id}' not found")

    # 2. Status validation
    status = (status or "issued").strip().lower()
    if status not in {"draft", "issued"}:
        raise InvoiceStateTransitionError(
            f"Initial invoice status must be 'draft' or 'issued', got '{status}'"
        )

    # 3. Order verification (if linked)
    order: Order | None = None
    if order_id:
        order = (
            db.query(Order)
            .options(selectinload(Order.items).selectinload(OrderItem.test))
            .filter(Order.id == order_id, Order.tenant_id == tenant_id)
            .first()
        )
        if not order:
            raise NotFoundError(f"Order '{order_id}' not found")
        if not branch_id and order.branch_id:
            branch_id = order.branch_id
        if not referral_partner_id and order.referral_partner_id:
            referral_partner_id = order.referral_partner_id

    target_branch_id = branch_id or tenant_context.branch_id

    # Verify referral partner belongs to tenant if provided
    if referral_partner_id:
        ref_partner = (
            db.query(ReferralPartner)
            .filter(ReferralPartner.id == referral_partner_id, ReferralPartner.tenant_id == tenant_id)
            .first()
        )
        if not ref_partner:
            raise NotFoundError(f"Referral partner '{referral_partner_id}' not found")

    # 4. Resolve / normalize line items
    raw_items = list(items or [])

    if not raw_items and order:
        for order_item in order.items:
            desc = order_item.test.name if order_item.test else (order_item.profile_name or "Lab Test")
            raw_items.append({
                "order_item_id": order_item.id,
                "item_type": "test",
                "item_id": order_item.test_id,
                "description": desc,
                "qty": 1.0,
            })

    if not raw_items:
        raise ValidationError("Invoice must contain at least one line item", field="items")

    invoice_id = str(uuid.uuid4())
    invoice_no = generate_invoice_no(db, tenant_id)

    calculated_items: list[InvoiceItem] = []
    line_audit_snapshots: list[dict[str, Any]] = []

    subtotal_accum = Decimal("0.00")
    discount_accum = Decimal("0.00")
    tax_accum = Decimal("0.00")
    grand_total_accum = Decimal("0.00")
    for idx, item_data in enumerate(raw_items):
        item_type = str(item_data.get("item_type", "test")).strip().lower()
        item_id = item_data.get("item_id")
        order_item_id = item_data.get("order_item_id")
        desc = (item_data.get("description") or "").strip()
        if not desc:
            desc = f"Item {idx + 1}"

        qty = Decimal(str(item_data.get("qty", 1.0)))
        if qty <= 0:
            raise ValidationError(f"Item {idx + 1} quantity must be greater than zero", field="qty")

        explicit_price = item_data.get("unit_price")
        if explicit_price is not None:
            unit_price = Decimal(str(explicit_price))
            if unit_price < 0:
                raise ValidationError(f"Item {idx + 1} unit price cannot be negative", field="unit_price")
        elif item_id and item_type in {"test", "profile", "package"}:
            resolved = resolve_pricing_rate(
                db,
                tenant_context=tenant_context,
                item_type=item_type,
                item_id=item_id,
                branch_id=target_branch_id,
            )
            unit_price = Decimal(str(resolved["rate"]))
        else:
            unit_price = Decimal("0.00")

        gross_amount = qty * unit_price

        raw_discount_pct = item_data.get("discount_pct")
        raw_discount_amt = item_data.get("discount_amount")

        # Resolve line discount through discount engine
        resolved_discount = calculate_line_discount(
            db,
            tenant_context=tenant_context,
            unit_price=unit_price,
            qty=qty,
            item_type=item_type,
            item_id=item_id,
            referral_partner_id=referral_partner_id,
            manual_discount_pct=Decimal(str(raw_discount_pct)) if raw_discount_pct is not None else None,
            manual_discount_amount=Decimal(str(raw_discount_amt)) if raw_discount_amt is not None else None,
            override_reason=item_data.get("discount_override_reason"),
            branch_id=target_branch_id,
            actor_user_id=actor_user_id,
        )

        discount_amount = resolved_discount.discount_amount
        discount_pct = resolved_discount.discount_pct

        tax_rate_pct = Decimal(str(item_data.get("tax_rate_pct", 0.0)))
        explicit_tax_amt = item_data.get("tax_amount")
        net_after_discount = gross_amount - discount_amount

        if explicit_tax_amt is not None:
            tax_amount = Decimal(str(explicit_tax_amt))
            if tax_amount < 0:
                raise ValidationError(f"Item {idx + 1} tax amount cannot be negative", field="tax_amount")
        elif tax_rate_pct > 0:
            tax_amount = (net_after_discount * (tax_rate_pct / Decimal("100"))).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            tax_amount = Decimal("0.00")

        line_total = net_after_discount + tax_amount

        subtotal_accum += gross_amount
        discount_accum += discount_amount
        tax_accum += tax_amount
        grand_total_accum += line_total

        inv_item = InvoiceItem(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            invoice_id=invoice_id,
            order_item_id=order_item_id,
            item_type=item_type,
            item_id=str(item_id) if item_id else None,
            description=desc,
            qty=float(qty),
            unit_price=float(unit_price),
            discount_pct=float(discount_pct),
            discount_amount=float(discount_amount),
            tax_rate_pct=float(tax_rate_pct),
            tax_amount=float(tax_amount),
            line_total=float(line_total),
        )
        calculated_items.append(inv_item)

        line_audit_snapshots.append({
            "item_id": inv_item.id,
            "description": inv_item.description,
            "item_type": inv_item.item_type,
            "target_id": inv_item.item_id,
            "qty": inv_item.qty,
            "unit_price": inv_item.unit_price,
            "discount_amount": inv_item.discount_amount,
            "tax_amount": inv_item.tax_amount,
            "line_total": inv_item.line_total,
        })
    invoice = Invoice(
        id=invoice_id,
        tenant_id=tenant_id,
        branch_id=target_branch_id,
        patient_id=patient_id,
        order_id=order_id,
        referral_partner_id=referral_partner_id,
        invoice_no=invoice_no,
        status=status,
        currency=(currency or "USD").strip().upper(),
        subtotal=float(subtotal_accum.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        discount_total=float(discount_accum.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        tax_total=float(tax_accum.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        grand_total=float(grand_total_accum.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        paid_amount=0.0,
        notes=notes.strip() if notes else None,
    )
    invoice.items = calculated_items

    db.add(invoice)
    db.flush()

    # Durable Line-Level Audit Trail
    log_audit_event(
        db,
        tenant_id=tenant_id,
        actor_user_id=actor_user_id or tenant_context.user_id,
        action_code="invoice.created",
        entity_type="invoice",
        entity_id=invoice.id,
        branch_id=invoice.branch_id,
        after_json={
            "invoice_no": invoice.invoice_no,
            "patient_id": invoice.patient_id,
            "order_id": invoice.order_id,
            "status": invoice.status,
            "currency": invoice.currency,
            "subtotal": invoice.subtotal,
            "discount_total": invoice.discount_total,
            "tax_total": invoice.tax_total,
            "grand_total": invoice.grand_total,
            "line_items_count": len(calculated_items),
            "line_items": line_audit_snapshots,
        },
    )

    db.commit()
    db.refresh(invoice)
    return invoice


def get_invoice(
    db: Session,
    *,
    tenant_context: TenantContext,
    invoice_id: str,
) -> Invoice:
    """Fetch invoice by ID ensuring multi-tenant isolation and loading line items."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    stmt = (
        select(Invoice)
        .options(joinedload(Invoice.items))
        .where(
            Invoice.tenant_id == tenant_context.tenant_id,
            Invoice.id == invoice_id,
        )
    )
    inv = db.execute(stmt).scalars().unique().first()
    if not inv:
        raise InvoiceNotFoundError(f"Invoice '{invoice_id}' not found")
    return inv


def list_invoices(
    db: Session,
    *,
    tenant_context: TenantContext,
    patient_id: str | None = None,
    order_id: str | None = None,
    branch_id: str | None = None,
    status: str | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Invoice], int]:
    """List invoices with tenant scoping and bounded pagination."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id

    clamped_limit = max(1, min(limit, 100))
    clamped_offset = max(0, offset)

    query = select(Invoice).where(Invoice.tenant_id == tenant_id)

    if patient_id:
        query = query.where(Invoice.patient_id == patient_id)
    if order_id:
        query = query.where(Invoice.order_id == order_id)
    if branch_id:
        query = query.where(Invoice.branch_id == branch_id)
    if status:
        query = query.where(Invoice.status == status.strip().lower())
    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.where(Invoice.invoice_no.ilike(search_pattern))

    count_query = select(func.count()).select_from(query.subquery())
    total_count = db.execute(count_query).scalar_one()

    stmt = (
        query.options(joinedload(Invoice.items))
        .order_by(Invoice.created_at.desc())
        .offset(clamped_offset)
        .limit(clamped_limit)
    )
    invoices = db.execute(stmt).scalars().unique().all()
    return list(invoices), total_count


def cancel_invoice(
    db: Session,
    *,
    tenant_context: TenantContext,
    invoice_id: str,
    reason: str,
    actor_user_id: str | None = None,
) -> Invoice:
    """
    Cancel an invoice with an authorized reason according to state machine rules.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    clean_reason = (reason or "").strip()
    if not clean_reason:
        raise ValidationError("Cancellation reason is required", field="reason")

    invoice = get_invoice(db, tenant_context=tenant_context, invoice_id=invoice_id)

    # Server-side authorization: verify user has 'billing.cancel' permission if user is provided
    effective_user_id = actor_user_id or tenant_context.user_id
    if effective_user_id:
        auth_user = (
            db.query(User)
            .filter(User.id == effective_user_id, User.tenant_id == tenant_context.tenant_id)
            .first()
        )
        if auth_user:
            if not authorize_action(db, auth_user, "billing.cancel", branch_id=invoice.branch_id):
                raise ForbiddenError("User is not authorized to cancel invoices ('billing.cancel' required)")

    allowed_targets = PERMITTED_INVOICE_TRANSITIONS.get(invoice.status, set())
    if "cancelled" not in allowed_targets:
        raise InvoiceStateTransitionError(
            f"Cannot cancel invoice in state '{invoice.status}'. Permitted from: draft, issued, part_paid."
        )

    prev_status = invoice.status
    invoice.status = "cancelled"
    invoice.cancellation_reason = clean_reason

    # Audit cancellation
    log_audit_event(
        db,
        tenant_id=tenant_context.tenant_id,
        actor_user_id=actor_user_id or tenant_context.user_id,
        action_code="invoice.cancelled",
        entity_type="invoice",
        entity_id=invoice.id,
        branch_id=invoice.branch_id,
        before_json={"status": prev_status},
        after_json={"status": "cancelled", "reason": clean_reason},
    )

    from app.billing.commission_service import cancel_commission_for_invoice
    cancel_commission_for_invoice(
        db,
        tenant_context=tenant_context,
        invoice_id=invoice.id,
        reason=clean_reason,
        actor_user_id=actor_user_id,
    )

    db.commit()
    db.refresh(invoice)
    return invoice




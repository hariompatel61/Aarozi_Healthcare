"""Discount Engine service implementing automatic referral and manual discount precedence, caps, and auditability."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session

from app.audit.service import log_audit_event
from app.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.billing import Invoice, InvoiceItem, PriceList, PriceListItem, ReferralPartner, ReferralRule
from app.models.identity import User
from app.rbac.engine import authorize_action
from app.security.tenant_guard import TenantContext, verify_tenant_boundary


@dataclass
class ResolvedItemDiscount:
    item_id: str | None
    item_type: str
    gross_amount: Decimal
    applied_source: str  # "manual", "referral", or "none"
    discount_pct: Decimal
    discount_amount: Decimal
    rule_id: str | None = None
    override_reason: str | None = None
    authorized_by: str | None = None


def _round_curr(val: Decimal | float) -> Decimal:
    d = Decimal(str(val))
    return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def resolve_referral_rule(
    db: Session,
    *,
    tenant_id: str,
    partner_id: str,
    item_type: str,
    item_id: str | None = None,
    department_id: str | None = None,
    as_of: datetime | None = None,
) -> ReferralRule | None:
    """
    Find matching active referral rule for given partner and item, ordered by priority.
    Precedence:
    1. Direct match on scope_type=item_type and scope_id=item_id
    2. Scope match on scope_type='department' and scope_id=department_id
    3. Global partner rule scope_type='all'
    """
    as_of = as_of or datetime.now(timezone.utc)

    query = (
        db.query(ReferralRule)
        .filter(
            ReferralRule.tenant_id == tenant_id,
            ReferralRule.partner_id == partner_id,
            ReferralRule.status == "active",
            ReferralRule.effective_from <= as_of,
            or_(ReferralRule.effective_to.is_(None), ReferralRule.effective_to >= as_of),
        )
        .order_by(ReferralRule.priority.asc(), ReferralRule.created_at.desc())
    )

    all_rules = query.all()
    if not all_rules:
        return None

    if item_id:
        for r in all_rules:
            if r.scope_type == item_type and r.scope_id == item_id:
                return r

    if department_id:
        for r in all_rules:
            if r.scope_type == "department" and r.scope_id == department_id:
                return r

    for r in all_rules:
        if r.scope_type == "all" or r.scope_id is None:
            return r

    return None


def calculate_line_discount(
    db: Session,
    *,
    tenant_context: TenantContext,
    unit_price: Decimal,
    qty: Decimal,
    item_type: str = "test",
    item_id: str | None = None,
    referral_partner_id: str | None = None,
    manual_discount_pct: Decimal | None = None,
    manual_discount_amount: Decimal | None = None,
    discount_mode_preference: str = "manual_precedence",
    authorizer_user: User | None = None,
    actor_user_id: str | None = None,
    override_reason: str | None = None,
    max_discount_cap_pct: Decimal | None = None,
    branch_id: str | None = None,
    department_id: str | None = None,
    as_of: datetime | None = None,
) -> ResolvedItemDiscount:
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id

    gross = _round_curr(unit_price * qty)
    if gross <= Decimal("0.00"):
        return ResolvedItemDiscount(
            item_id=item_id,
            item_type=item_type,
            gross_amount=gross,
            applied_source="none",
            discount_pct=Decimal("0.00"),
            discount_amount=Decimal("0.00"),
        )

    referral_rule = None
    ref_discount_pct = Decimal("0.00")
    if referral_partner_id:
        referral_rule = resolve_referral_rule(
            db,
            tenant_id=tenant_id,
            partner_id=referral_partner_id,
            item_type=item_type,
            item_id=item_id,
            department_id=department_id,
            as_of=as_of,
        )
        if referral_rule:
            ref_discount_pct = Decimal(str(referral_rule.patient_discount_pct))

    ref_discount_amount = _round_curr(gross * (ref_discount_pct / Decimal("100")))

    has_manual = False
    man_pct = Decimal("0.00")
    man_amt = Decimal("0.00")

    if manual_discount_amount is not None:
        has_manual = True
        man_amt = _round_curr(Decimal(str(manual_discount_amount)))
        if man_amt < Decimal("0.00") or man_amt > gross:
            raise ValidationError("Manual discount amount cannot exceed line gross amount", field="manual_discount_amount")
        if gross > Decimal("0.00"):
            man_pct = _round_curr((man_amt / gross) * Decimal("100"))
    elif manual_discount_pct is not None and Decimal(str(manual_discount_pct)) > Decimal("0.00"):
        has_manual = True
        man_pct = Decimal(str(manual_discount_pct))
        if man_pct > Decimal("100.00") or man_pct < Decimal("0.00"):
            raise ValidationError("Manual discount percentage must be between 0 and 100", field="manual_discount_pct")
        man_amt = _round_curr(gross * (man_pct / Decimal("100")))

    effective_cap = max_discount_cap_pct
    if effective_cap is None and item_id:
        pli = (
            db.query(PriceListItem)
            .join(PriceList, PriceListItem.price_list_id == PriceList.id)
            .filter(
                PriceList.tenant_id == tenant_id,
                PriceListItem.item_type == item_type,
                PriceListItem.item_id == item_id,
                PriceListItem.is_active.is_(True),
            )
            .first()
        )
        if pli and pli.max_discount_pct > 0:
            effective_cap = Decimal(str(pli.max_discount_pct))

    selected_source = "none"
    chosen_pct = Decimal("0.00")
    chosen_amt = Decimal("0.00")

    if has_manual and referral_rule:
        if discount_mode_preference == "best_for_patient":
            if man_amt >= ref_discount_amount:
                selected_source = "manual"
                chosen_pct = man_pct
                chosen_amt = man_amt
            else:
                selected_source = "referral"
                chosen_pct = ref_discount_pct
                chosen_amt = ref_discount_amount
        elif discount_mode_preference == "referral_precedence":
            selected_source = "referral"
            chosen_pct = ref_discount_pct
            chosen_amt = ref_discount_amount
        else:
            selected_source = "manual"
            chosen_pct = man_pct
            chosen_amt = man_amt
    elif has_manual:
        selected_source = "manual"
        chosen_pct = man_pct
        chosen_amt = man_amt
    elif referral_rule:
        selected_source = "referral"
        chosen_pct = ref_discount_pct
        chosen_amt = ref_discount_amount

    authorized_by_id = None
    if selected_source == "manual" and chosen_amt > Decimal("0.00"):
        if authorizer_user is not None:
            authorized = authorize_action(
                db,
                authorizer_user,
                "billing.discount",
                branch_id=branch_id,
            )
            if not authorized:
                raise ForbiddenError("User is not authorized to grant discounts ('billing.discount' permission required)")
            authorized_by_id = authorizer_user.id
        elif tenant_context.user_id:
            current_u = db.query(User).filter(User.id == tenant_context.user_id, User.tenant_id == tenant_id).first()
            if current_u:
                authorized = authorize_action(db, current_u, "billing.discount", branch_id=branch_id)
                if not authorized:
                    raise ForbiddenError("User is not authorized to grant discounts ('billing.discount' permission required)")
                authorized_by_id = current_u.id

        if effective_cap is not None and chosen_pct > effective_cap:
            if not override_reason or not override_reason.strip():
                raise ValidationError(
                    f"Discount {chosen_pct}% exceeds maximum cap {effective_cap}%. An override reason is required.",
                    field="discount_cap",
                )

    return ResolvedItemDiscount(
        item_id=item_id,
        item_type=item_type,
        gross_amount=gross,
        applied_source=selected_source,
        discount_pct=chosen_pct,
        discount_amount=chosen_amt,
        rule_id=referral_rule.id if selected_source == "referral" and referral_rule else None,
        override_reason=override_reason if (effective_cap is not None and chosen_pct > effective_cap) else None,
        authorized_by=authorized_by_id,
    )



def apply_discount_to_invoice(
    db: Session,
    *,
    tenant_context: TenantContext,
    invoice_id: str,
    discount_pct: float | None = None,
    discount_amount: float | None = None,
    override_reason: str | None = None,
    authorizer_user: User | None = None,
    actor_user_id: str | None = None,
) -> Invoice:
    """
    Apply or update discount on an existing draft/issued invoice, recalculating line items and invoice totals.
    Emits 'discount.applied' audit event.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id

    invoice = (
        db.query(Invoice)
        .filter(Invoice.id == invoice_id, Invoice.tenant_id == tenant_id)
        .first()
    )
    if not invoice:
        raise NotFoundError(f"Invoice '{invoice_id}' not found")

    if invoice.status not in {"draft", "issued"}:
        raise ConflictError(f"Cannot apply discount to invoice in '{invoice.status}' status")

    actor_id = actor_user_id or tenant_context.user_id
    auth_user = authorizer_user
    if not auth_user and actor_id:
        auth_user = db.query(User).filter(User.id == actor_id, User.tenant_id == tenant_id).first()

    if auth_user:
        if not authorize_action(db, auth_user, "billing.discount", branch_id=invoice.branch_id):
            raise ForbiddenError("User is not authorized to grant discounts ('billing.discount' permission required)")

    subtotal = Decimal(str(invoice.subtotal))
    if subtotal <= Decimal("0.00"):
        raise ValidationError("Cannot apply discount to invoice with 0 subtotal", field="subtotal")

    if discount_amount is not None:
        disc_amt = _round_curr(Decimal(str(discount_amount)))
        if disc_amt < Decimal("0.00") or disc_amt > subtotal:
            raise ValidationError("Discount amount cannot exceed invoice subtotal", field="discount_amount")
        disc_pct = _round_curr((disc_amt / subtotal) * Decimal("100"))
    elif discount_pct is not None:
        disc_pct = _round_curr(Decimal(str(discount_pct)))
        if disc_pct < Decimal("0.00") or disc_pct > Decimal("100.00"):
            raise ValidationError("Discount percentage must be between 0 and 100", field="discount_pct")
        disc_amt = _round_curr(subtotal * (disc_pct / Decimal("100")))
    else:
        raise ValidationError("Either discount_pct or discount_amount must be provided")

    total_tax = Decimal("0.00")
    total_net = Decimal("0.00")
    total_discount = Decimal("0.00")

    items = invoice.items
    num_items = len(items)
    allocated_discount = Decimal("0.00")

    for idx, itm in enumerate(items):
        item_gross = Decimal(str(itm.qty)) * Decimal(str(itm.unit_price))
        if idx == num_items - 1:
            item_disc = disc_amt - allocated_discount
        else:
            item_disc = _round_curr(disc_amt * (item_gross / subtotal)) if subtotal > 0 else Decimal("0.00")
            allocated_discount += item_disc

        itm.discount_amount = float(item_disc)
        itm.discount_pct = float(_round_curr((item_disc / item_gross) * Decimal("100"))) if item_gross > 0 else 0.0

        item_net = item_gross - item_disc
        tax_pct = Decimal(str(itm.tax_rate_pct))
        item_tax = _round_curr(item_net * (tax_pct / Decimal("100"))) if tax_pct > 0 else Decimal("0.00")
        itm.tax_amount = float(item_tax)
        itm.line_total = float(item_net + item_tax)

        total_discount += item_disc
        total_tax += item_tax
        total_net += item_net

    invoice.discount_total = float(total_discount)
    invoice.tax_total = float(total_tax)
    invoice.grand_total = float(total_net + total_tax)
    if override_reason:
        existing_notes = invoice.notes or ""
        invoice.notes = f"{existing_notes}\nDiscount Override: {override_reason}".strip()

    db.flush()

    log_audit_event(
        db,
        tenant_id=tenant_id,
        actor_user_id=actor_id,
        action_code="discount.applied",
        entity_type="invoice",
        entity_id=invoice.id,
        branch_id=invoice.branch_id,
        after_json={
            "invoice_no": invoice.invoice_no,
            "discount_total": float(total_discount),
            "grand_total": float(invoice.grand_total),
            "override_reason": override_reason,
        },
    )

    return invoice



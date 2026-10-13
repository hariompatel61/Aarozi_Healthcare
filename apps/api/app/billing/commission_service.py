"""Referral Commission Ledger service: rule resolution, accrual, settlement, RBAC, and audit trail."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy import func, select, or_
from sqlalchemy.orm import Session

from app.audit.service import log_audit_event
from app.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.billing import CommissionLedger, Invoice, InvoiceItem, ReferralPartner, ReferralRule
from app.models.identity import User
from app.models.pathology import Test
from app.rbac.engine import authorize_action
from app.security.tenant_guard import TenantContext, verify_tenant_boundary


class CommissionLedgerNotFoundError(NotFoundError):
    """Raised when a commission ledger record is not found."""
    pass


def _round_curr(val: Decimal | float | int) -> Decimal:
    """Helper to round currency to 2 decimal places using half-up."""
    d = Decimal(str(val))
    return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _check_permission(
    db: Session,
    *,
    tenant_context: TenantContext,
    permission_code: str,
    actor_user_id: str | None = None,
) -> None:
    """Enforce server-side RBAC if user is present in context."""
    user_id = actor_user_id or tenant_context.user_id
    if not user_id:
        return
    user = db.query(User).filter(User.id == user_id, User.tenant_id == tenant_context.tenant_id).first()
    if user and not authorize_action(db, user, permission_code, branch_id=tenant_context.branch_id):
        raise ForbiddenError(f"User is not authorized for '{permission_code}'")


def resolve_commission_rule(
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


def calculate_line_commission(
    rule: ReferralRule,
    line_total: Decimal,
) -> Decimal:
    """Calculate commission for an invoice line given matched rule."""
    comm = Decimal("0.00")
    if rule.commission_pct and Decimal(str(rule.commission_pct)) > Decimal("0.00"):
        pct = Decimal(str(rule.commission_pct))
        comm += _round_curr(line_total * (pct / Decimal("100")))
    if rule.commission_fixed and Decimal(str(rule.commission_fixed)) > Decimal("0.00"):
        comm += _round_curr(Decimal(str(rule.commission_fixed)))
    return comm



def accrue_commission_for_invoice(
    db: Session,
    *,
    tenant_context: TenantContext,
    invoice_id: str,
    actor_user_id: str | None = None,
    as_of: datetime | None = None,
) -> CommissionLedger | None:
    """
    Resolve referral rules for each line item of an invoice and accrue commission to the ledger.
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

    if not invoice.referral_partner_id:
        return None

    if invoice.status == "cancelled":
        raise ConflictError("Cannot accrue commission for a cancelled invoice")

    existing = (
        db.query(CommissionLedger)
        .filter(CommissionLedger.tenant_id == tenant_id, CommissionLedger.invoice_id == invoice.id)
        .all()
    )
    for entry in existing:
        if entry.status == "settled":
            raise ConflictError(f"Commission for invoice '{invoice_id}' has already been settled")

    for entry in existing:
        if entry.status in {"pending", "accrued"}:
            db.delete(entry)
    db.flush()

    total_commission = Decimal("0.00")
    breakdown: list[dict[str, Any]] = []
    now_ts = as_of or datetime.now(timezone.utc)

    for item in invoice.items:
        line_total = _round_curr(item.line_total)
        dept_id = None
        if item.item_type == "test" and item.item_id:
            test_obj = db.query(Test).filter(Test.id == item.item_id, Test.tenant_id == tenant_id).first()
            if test_obj:
                dept_id = test_obj.department_id

        rule = resolve_commission_rule(
            db,
            tenant_id=tenant_id,
            partner_id=invoice.referral_partner_id,
            item_type=item.item_type,
            item_id=item.item_id,
            department_id=dept_id,
            as_of=now_ts,
        )

        item_comm = Decimal("0.00")
        rule_id = None
        comm_pct = 0.0
        comm_fixed = None

        if rule:
            rule_id = rule.id
            comm_pct = float(rule.commission_pct)
            comm_fixed = float(rule.commission_fixed) if rule.commission_fixed is not None else None
            item_comm = calculate_line_commission(rule, line_total)

        total_commission += item_comm
        breakdown.append({
            "item_id": item.item_id,
            "description": item.description,
            "line_total": float(line_total),
            "rule_id": rule_id,
            "commission_pct": comm_pct,
            "commission_fixed": comm_fixed,
            "commission_amount": float(item_comm),
        })

    total_rounded = _round_curr(total_commission)

    ledger = CommissionLedger(
        tenant_id=tenant_id,
        referral_partner_id=invoice.referral_partner_id,
        invoice_id=invoice.id,
        amount=float(total_rounded),
        status="pending",
        calculated_at=now_ts,
        breakdown_json=json.dumps(breakdown),
    )
    db.add(ledger)
    db.flush()

    log_audit_event(
        db,
        tenant_id=tenant_id,
        action_code="referral.commission.calculated",
        actor_user_id=actor_user_id or tenant_context.user_id,
        entity_type="commission_ledger",
        entity_id=ledger.id,
        after_json={
            "invoice_id": invoice.id,
            "referral_partner_id": invoice.referral_partner_id,
            "amount": float(total_rounded),
            "status": "pending",
        },
    )

    db.commit()
    db.refresh(ledger)
    return ledger


def accrue_manual_commission(
    db: Session,
    *,
    tenant_context: TenantContext,
    referral_partner_id: str,
    amount: float | Decimal,
    invoice_id: str | None = None,
    notes: str | None = None,
    actor_user_id: str | None = None,
) -> CommissionLedger:
    """Manually accrue commission for a referral partner."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id

    _check_permission(
        db,
        tenant_context=tenant_context,
        permission_code="referral.commission.settle",
        actor_user_id=actor_user_id,
    )

    partner = (
        db.query(ReferralPartner)
        .filter(ReferralPartner.id == referral_partner_id, ReferralPartner.tenant_id == tenant_id)
        .first()
    )
    if not partner:
        raise NotFoundError(f"Referral partner '{referral_partner_id}' not found")

    amt = _round_curr(amount)
    if amt < Decimal("0.00"):
        raise ValidationError("Commission amount cannot be negative", field="amount")

    ledger = CommissionLedger(
        tenant_id=tenant_id,
        referral_partner_id=referral_partner_id,
        invoice_id=invoice_id,
        amount=float(amt),
        status="pending",
        notes=notes,
        calculated_at=datetime.now(timezone.utc),
    )
    db.add(ledger)
    db.flush()

    log_audit_event(
        db,
        tenant_id=tenant_id,
        action_code="referral.commission.accrued",
        actor_user_id=actor_user_id or tenant_context.user_id,
        entity_type="commission_ledger",
        entity_id=ledger.id,
        after_json={
            "referral_partner_id": referral_partner_id,
            "amount": float(amt),
            "status": "pending",
            "notes": notes,
        },
    )

    db.commit()
    db.refresh(ledger)
    return ledger


def settle_commission(
    db: Session,
    *,
    tenant_context: TenantContext,
    ledger_ids: list[str] | None = None,
    referral_partner_id: str | None = None,
    settlement_reference: str | None = None,
    notes: str | None = None,
    actor_user_id: str | None = None,
) -> list[CommissionLedger]:
    """
    Settle pending commission records with RBAC authorization and audit logging.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id

    _check_permission(
        db,
        tenant_context=tenant_context,
        permission_code="referral.commission.settle",
        actor_user_id=actor_user_id,
    )

    query = db.query(CommissionLedger).filter(
        CommissionLedger.tenant_id == tenant_id,
        CommissionLedger.status == "pending",
    )

    if ledger_ids is not None:
        if not ledger_ids:
            raise ValidationError("ledger_ids list cannot be empty when provided", field="ledger_ids")
        query = query.filter(CommissionLedger.id.in_(ledger_ids))

    if referral_partner_id:
        query = query.filter(CommissionLedger.referral_partner_id == referral_partner_id)

    records = query.all()
    if not records:
        raise NotFoundError("No pending commission ledger entries found matching criteria")

    settled_now = datetime.now(timezone.utc)
    effective_user_id = actor_user_id or tenant_context.user_id

    for rec in records:
        before_state = {"status": rec.status, "amount": float(rec.amount)}
        rec.status = "settled"
        rec.settled_at = settled_now
        rec.settled_by = effective_user_id
        if settlement_reference:
            rec.settlement_reference = settlement_reference
        if notes:
            rec.notes = notes

        log_audit_event(
            db,
            tenant_id=tenant_id,
            action_code="referral.commission.settled",
            actor_user_id=effective_user_id,
            entity_type="commission_ledger",
            entity_id=rec.id,
            before_json=before_state,
            after_json={
                "status": "settled",
                "settled_at": settled_now.isoformat(),
                "settlement_reference": settlement_reference,
            },
        )

    db.commit()
    for rec in records:
        db.refresh(rec)
    return records


def cancel_commission_for_invoice(
    db: Session,
    *,
    tenant_context: TenantContext,
    invoice_id: str,
    reason: str,
    actor_user_id: str | None = None,
) -> list[CommissionLedger]:
    """Cancel pending commissions when an invoice is cancelled."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id

    records = (
        db.query(CommissionLedger)
        .filter(
            CommissionLedger.tenant_id == tenant_id,
            CommissionLedger.invoice_id == invoice_id,
            CommissionLedger.status == "pending",
        )
        .all()
    )

    effective_user_id = actor_user_id or tenant_context.user_id
    for rec in records:
        before_state = {"status": rec.status}
        rec.status = "cancelled"
        rec.notes = f"Cancelled: {reason}"

        log_audit_event(
            db,
            tenant_id=tenant_id,
            action_code="referral.commission.cancelled",
            actor_user_id=effective_user_id,
            entity_type="commission_ledger",
            entity_id=rec.id,
            before_json=before_state,
            after_json={"status": "cancelled", "reason": reason},
        )

    db.commit()
    for rec in records:
        db.refresh(rec)
    return records


def get_commission_ledger(
    db: Session,
    *,
    tenant_context: TenantContext,
    ledger_id: str,
    actor_user_id: str | None = None,
) -> CommissionLedger:
    """Retrieve single commission ledger record enforcing tenant isolation and RBAC."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    _check_permission(
        db,
        tenant_context=tenant_context,
        permission_code="referral.commission.view",
        actor_user_id=actor_user_id,
    )

    ledger = (
        db.query(CommissionLedger)
        .filter(
            CommissionLedger.id == ledger_id,
            CommissionLedger.tenant_id == tenant_context.tenant_id,
        )
        .first()
    )
    if not ledger:
        raise CommissionLedgerNotFoundError(f"Commission ledger entry '{ledger_id}' not found")
    return ledger


def list_commission_ledgers(
    db: Session,
    *,
    tenant_context: TenantContext,
    referral_partner_id: str | None = None,
    invoice_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    actor_user_id: str | None = None,
) -> tuple[list[CommissionLedger], int]:
    """List commission ledger entries with pagination, filters, and RBAC view enforcement."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    _check_permission(
        db,
        tenant_context=tenant_context,
        permission_code="referral.commission.view",
        actor_user_id=actor_user_id,
    )

    limit = min(max(1, limit), 100)
    offset = max(0, offset)

    query = db.query(CommissionLedger).filter(CommissionLedger.tenant_id == tenant_context.tenant_id)

    if referral_partner_id:
        query = query.filter(CommissionLedger.referral_partner_id == referral_partner_id)
    if invoice_id:
        query = query.filter(CommissionLedger.invoice_id == invoice_id)
    if status:
        query = query.filter(CommissionLedger.status == status)

    total_count = query.count()
    items = query.order_by(CommissionLedger.calculated_at.desc()).offset(offset).limit(limit).all()

    return items, total_count


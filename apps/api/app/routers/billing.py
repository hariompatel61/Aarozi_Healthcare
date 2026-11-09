"""Billing, Invoicing, Payment Collection, and Referral Accounting API router."""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.billing import Invoice, Payment, ReferralPartner, PriceList, CommissionLedger
from app.models.patient import Patient
from app.models.pathology import Order
from app.billing.invoice_service import (
    create_invoice,
    get_invoice,
    list_invoices,
    cancel_invoice,
    InvoiceNotFoundError,
    InvoiceStateTransitionError,
)
from app.billing.payment_service import record_payment, get_payment
from app.billing.pricing_service import list_price_lists
from app.billing.referral_service import create_referral_partner, list_referral_partners
from app.billing.commission_service import list_commission_ledgers, settle_commission
from app.rbac.engine import enforce_permission
from app.security.auth import get_current_user
from app.security.tenant_guard import get_tenant_context, TenantContext

router = APIRouter(prefix="/billing", tags=["billing"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class InvoiceItemInput(BaseModel):
    order_item_id: str | None = None
    item_type: str = "test"
    item_id: str | None = None
    description: str
    quantity: int = 1
    unit_price: float
    discount_amount: float = 0.0
    tax_amount: float = 0.0


class InvoiceCreateRequest(BaseModel):
    patient_id: str
    order_id: str | None = None
    referral_partner_id: str | None = None
    branch_id: str | None = None
    currency: str = "USD"
    status: str = "issued"
    notes: str | None = None
    items: list[InvoiceItemInput] | None = None


class PaymentRecordRequest(BaseModel):
    invoice_id: str
    amount: float = Field(..., gt=0.0)
    method: str = "cash"
    provider_reference: str | None = None
    idempotency_key: str | None = None
    notes: str | None = None


class ReferralPartnerCreateRequest(BaseModel):
    name: str
    partner_type: str = "doctor"
    specialty: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    commission_type: str = "percentage"
    commission_value: float = 0.0


class CommissionSettleRequest(BaseModel):
    partner_id: str
    ledger_ids: list[str] | None = None
    settlement_reference: str
    notes: str | None = None


# ---------------------------------------------------------------------------
# Invoice Endpoints
# ---------------------------------------------------------------------------

@router.post("/invoices/create", status_code=status.HTTP_201_CREATED)
def generate_invoice(
    payload: InvoiceCreateRequest,
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_tenant_context),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    """Generate invoice directly or auto-populate from clinical lab order."""
    enforce_permission(db, current_user, "invoice.create")

    items_dict = [i.model_dump() for i in payload.items] if payload.items else None
    try:
        inv = create_invoice(
            db,
            tenant_context=tenant_context,
            patient_id=payload.patient_id,
            order_id=payload.order_id,
            referral_partner_id=payload.referral_partner_id,
            branch_id=payload.branch_id,
            currency=payload.currency,
            status=payload.status,
            notes=payload.notes,
            items=items_dict,
            actor_user_id=getattr(current_user, "id", None),
        )
        db.commit()
        db.refresh(inv)
    except Exception as err:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    subtotal = float(inv.subtotal) if inv.subtotal is not None else 0.0
    discount = float(getattr(inv, "discount_total", getattr(inv, "discount_amount", 0.0)) or 0.0)
    tax = float(getattr(inv, "tax_total", getattr(inv, "tax_amount", 0.0)) or 0.0)
    total = float(getattr(inv, "grand_total", getattr(inv, "total_amount", 0.0)) or 0.0)
    paid = float(inv.paid_amount or 0.0)
    balance = float(getattr(inv, "balance_amount", total - paid) or 0.0)

    return {
        "id": inv.id,
        "invoice_no": inv.invoice_no,
        "patient_id": inv.patient_id,
        "order_id": inv.order_id,
        "subtotal": subtotal,
        "discount_amount": discount,
        "tax_amount": tax,
        "total_amount": total,
        "paid_amount": paid,
        "balance_amount": balance,
        "status": inv.status,
        "currency": inv.currency,
        "created_at": inv.created_at.isoformat() if inv.created_at else None,
    }


@router.get("/invoices")
def get_invoices(
    patient_id: str | None = None,
    order_id: str | None = None,
    referral_partner_id: str | None = None,
    search: str | None = None,
    status: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_tenant_context),
    current_user: Any = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """List invoices with bounded pagination, status filters, and relational details."""
    enforce_permission(db, current_user, "invoice.view")

    limit_val = limit if isinstance(limit, int) else 50
    offset_val = offset if isinstance(offset, int) else 0

    invoices, total_count = list_invoices(
        db,
        tenant_context=tenant_context,
        patient_id=patient_id,
        order_id=order_id,
        referral_partner_id=referral_partner_id,
        status=status,
        search=search,
        limit=limit_val,
        offset=offset_val,
    )
    result = []
    for inv in invoices:
        patient = db.query(Patient).filter(Patient.id == inv.patient_id).first()
        patient_name = patient.full_name if patient else "Walk-in Patient"
        patient_uhid = patient.patient_no if patient else (inv.patient_id or "N/A")

        doctor_name = "Self / Direct"
        if inv.referral_partner_id:
            partner = db.query(ReferralPartner).filter(ReferralPartner.id == inv.referral_partner_id).first()
            if partner:
                doctor_name = partner.name

        test_names = ", ".join([itm.description for itm in inv.items]) if inv.items else "Diagnostic Panel"
        total = float(getattr(inv, "grand_total", getattr(inv, "total_amount", 0.0)) or 0.0)
        paid = float(inv.paid_amount or 0.0)
        balance = float(getattr(inv, "balance_amount", total - paid) or 0.0)

        result.append({
            "id": inv.id,
            "invoice_no": inv.invoice_no,
            "patient_id": inv.patient_id,
            "patient_name": patient_name,
            "patient_uhid": patient_uhid,
            "order_id": inv.order_id,
            "referral_partner_id": inv.referral_partner_id,
            "doctor_name": doctor_name,
            "tests": test_names,
            "total_amount": total,
            "paid_amount": paid,
            "balance_amount": balance,
            "status": inv.status,
            "currency": inv.currency,
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
        })
    return result


@router.get("/invoices/{invoice_id}")
def get_invoice_details(
    invoice_id: str,
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_tenant_context),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    """Retrieve full invoice details with line items and payment transactions."""
    enforce_permission(db, current_user, "invoice.view")

    try:
        inv = get_invoice(db, tenant_context=tenant_context, invoice_id=invoice_id)
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))

    return {
        "id": inv.id,
        "invoice_no": inv.invoice_no,
        "patient_id": inv.patient_id,
        "order_id": inv.order_id,
        "subtotal": float(inv.subtotal) if inv.subtotal is not None else 0.0,
        "discount_amount": float(getattr(inv, "discount_total", getattr(inv, "discount_amount", 0.0)) or 0.0),
        "tax_amount": float(getattr(inv, "tax_total", getattr(inv, "tax_amount", 0.0)) or 0.0),
        "total_amount": float(getattr(inv, "grand_total", getattr(inv, "total_amount", 0.0)) or 0.0),
        "paid_amount": float(inv.paid_amount or 0.0),
        "balance_amount": float(getattr(inv, "balance_amount", (getattr(inv, "grand_total", getattr(inv, "total_amount", 0.0)) or 0.0) - (inv.paid_amount or 0.0)) or 0.0),
        "status": inv.status,
        "currency": inv.currency,
        "notes": inv.notes,
        "items": [
            {
                "id": itm.id,
                "description": itm.description,
                "quantity": float(getattr(itm, "qty", getattr(itm, "quantity", 1.0)) or 1.0),
                "unit_price": float(itm.unit_price or 0.0),
                "discount_amount": float(itm.discount_amount or 0.0),
                "tax_amount": float(itm.tax_amount or 0.0),
                "net_amount": float(getattr(itm, "line_total", getattr(itm, "net_amount", 0.0)) or 0.0),
            }
            for itm in inv.items
        ],
        "payments": [
            {
                "id": p.id,
                "receipt_no": p.receipt_no,
                "amount": float(p.amount),
                "method": p.method,
                "status": p.status,
                "received_at": p.received_at.isoformat() if p.received_at else None,
            }
            for p in inv.payments
        ],
    }


@router.post("/invoices/{invoice_id}/cancel")
def cancel_existing_invoice(
    invoice_id: str,
    reason: str = Query(..., min_length=3),
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_tenant_context),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    """Cancel invoice with audit reason."""
    enforce_permission(db, current_user, "invoice.cancel")

    try:
        inv = cancel_invoice(
            db,
            tenant_context=tenant_context,
            invoice_id=invoice_id,
            reason=reason,
            actor_user_id=getattr(current_user, "id", None),
        )
        db.commit()
    except Exception as err:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    return {"id": inv.id, "invoice_no": inv.invoice_no, "status": inv.status}


# ---------------------------------------------------------------------------
# Payment Collection Endpoints
# ---------------------------------------------------------------------------

@router.post("/payments", status_code=status.HTTP_201_CREATED)
def collect_payment(
    payload: PaymentRecordRequest,
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_tenant_context),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    """Record receipt payment against invoice and update ledger/balance."""
    enforce_permission(db, current_user, "payment.record")

    try:
        payment = record_payment(
            db,
            tenant_context=tenant_context,
            invoice_id=payload.invoice_id,
            amount=payload.amount,
            method=payload.method,
            provider_reference=payload.provider_reference,
            idempotency_key=payload.idempotency_key,
            notes=payload.notes,
            actor_user_id=getattr(current_user, "id", None),
        )
        db.commit()
        db.refresh(payment)
    except Exception as err:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    return {
        "id": payment.id,
        "receipt_no": payment.receipt_no,
        "invoice_id": payment.invoice_id,
        "amount": float(payment.amount),
        "method": payment.method,
        "status": payment.status,
        "received_at": payment.received_at.isoformat() if payment.received_at else None,
    }


# ---------------------------------------------------------------------------
# Referral Partners & Commission Endpoints
# ---------------------------------------------------------------------------

@router.get("/referrals/partners")
def get_referral_partners(
    search: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_tenant_context),
    current_user: Any = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """List referring physicians and clinics with real-time relational stats."""
    enforce_permission(db, current_user, "billing.view")

    limit_val = limit if isinstance(limit, int) else 50
    offset_val = offset if isinstance(offset, int) else 0

    partners, total_count = list_referral_partners(
        db,
        tenant_context=tenant_context,
        search=search,
        limit=limit_val,
        offset=offset_val,
    )
    result = []
    for p in partners:
        cases_count = db.query(func.count(Order.id)).filter(
            Order.tenant_id == tenant_context.tenant_id,
            Order.referral_partner_id == p.id,
        ).scalar() or 0
        if cases_count == 0:
            cases_count = db.query(func.count(Invoice.id)).filter(
                Invoice.tenant_id == tenant_context.tenant_id,
                Invoice.referral_partner_id == p.id,
            ).scalar() or 0

        business_vol = db.query(func.sum(Invoice.grand_total)).filter(
            Invoice.tenant_id == tenant_context.tenant_id,
            Invoice.referral_partner_id == p.id,
        ).scalar() or 0.0

        unsettled = db.query(func.sum(CommissionLedger.amount)).filter(
            CommissionLedger.tenant_id == tenant_context.tenant_id,
            CommissionLedger.referral_partner_id == p.id,
            CommissionLedger.status.in_(["pending", "accrued"]),
        ).scalar() or 0.0

        comm_type = "percentage"
        comm_val = 15.0
        if p.rules:
            active_rule = next((r for r in p.rules if r.status == "active"), p.rules[0])
            if active_rule.commission_fixed and float(active_rule.commission_fixed) > 0:
                comm_type = "fixed"
                comm_val = float(active_rule.commission_fixed)
            else:
                comm_type = "percentage"
                comm_val = float(active_rule.commission_pct or 15.0)

        result.append({
            "id": p.id,
            "name": p.name,
            "partner_type": p.partner_type,
            "specialty": p.specialty or ("Consulting Physician" if p.partner_type == "doctor" else "Diagnostic Center"),
            "contact_phone": p.phone or "",
            "contact_email": p.email or "",
            "commission_type": comm_type,
            "commission_value": comm_val,
            "total_cases": int(cases_count),
            "business_volume": float(business_vol),
            "unsettled": float(unsettled),
            "status": p.status,
            "is_active": p.status == "active",
        })
    return result


@router.post("/referrals/partners/create", status_code=status.HTTP_201_CREATED)
def add_referral_partner(
    payload: ReferralPartnerCreateRequest,
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_tenant_context),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    """Register referring doctor or partner hospital."""
    enforce_permission(db, current_user, "billing.manage")

    try:
        partner = create_referral_partner(
            db,
            tenant_context=tenant_context,
            name=payload.name,
            partner_type=payload.partner_type,
            specialty=payload.specialty,
            phone=payload.contact_phone,
            email=payload.contact_email,
        )
        if payload.commission_value and payload.commission_value > 0:
            from app.billing.referral_service import create_referral_rule
            from decimal import Decimal
            try:
                create_referral_rule(
                    db,
                    tenant_context=tenant_context,
                    partner_id=partner.id,
                    scope_type="all",
                    commission_pct=Decimal(str(payload.commission_value)) if payload.commission_type == "percentage" else Decimal("0"),
                    commission_fixed=Decimal(str(payload.commission_value)) if payload.commission_type == "fixed" else Decimal("0"),
                    actor_user_id=getattr(current_user, "id", None),
                )
            except Exception:
                pass
        db.commit()
        db.refresh(partner)
    except Exception as err:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    return {"id": partner.id, "name": partner.name, "partner_type": partner.partner_type}


@router.post("/referrals/settle")
def settle_referral_commission(
    payload: CommissionSettleRequest,
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_tenant_context),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    """Settle commission for referral partner."""
    enforce_permission(db, current_user, "billing.manage")
    try:
        settled_records = settle_commission(
            db,
            tenant_context=tenant_context,
            referral_partner_id=payload.partner_id,
            ledger_ids=payload.ledger_ids,
            settlement_reference=payload.settlement_reference,
            notes=payload.notes,
            actor_user_id=getattr(current_user, "id", None),
        )
        return {"status": "success", "settled_count": len(settled_records)}
    except Exception as err:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.get("/referrals/commissions")
def get_commissions(
    partner_id: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_tenant_context),
    current_user: Any = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """List doctor referral commission accrual ledger."""
    enforce_permission(db, current_user, "billing.view")

    ledgers, total_count = list_commission_ledgers(
        db,
        tenant_context=tenant_context,
        referral_partner_id=partner_id,
        limit=limit,
        offset=offset,
    )
    return [
        {
            "id": l.id,
            "partner_id": l.referral_partner_id,
            "invoice_id": l.invoice_id,
            "commission_amount": float(l.amount),
            "status": l.status,
            "settled_at": l.settled_at.isoformat() if l.settled_at else None,
            "calculated_at": l.calculated_at.isoformat() if l.calculated_at else None,
        }
        for l in ledgers
    ]

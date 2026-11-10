"""Corporate Client Management and B2B Billing API router."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.corporate import CorporateAccount, CorporatePriceList, CorporateInvoice
from app.models.pathology import Test
from app.security.tenant_guard import get_tenant_context, TenantContext

router = APIRouter(prefix="/corporates", tags=["corporates"])


class CorporateAccountCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    code: str = Field(..., min_length=2, max_length=50)
    contact_person: str | None = None
    email: str | None = None
    phone: str | None = None
    gstin: str | None = None
    address: str | None = None
    credit_limit: float = 100000.0
    billing_cycle: str = "MONTHLY"  # MONTHLY, BIWEEKLY, PER_ORDER


class CorporatePriceItemSet(BaseModel):
    test_id: str
    special_rate: float | None = None
    discount_pct: float | None = None


class CorporateInvoiceCreate(BaseModel):
    period_start: datetime
    period_end: datetime
    total_amount: float = Field(..., gt=0)
    due_days: int = 30


@router.get("")
def list_corporates(
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    corps = (
        db.query(CorporateAccount)
        .filter(CorporateAccount.tenant_id == tenant_ctx.tenant_id, CorporateAccount.is_active == True)  # noqa: E712
        .order_by(CorporateAccount.name.asc())
        .all()
    )

    # Auto-seed mock corporate clients if empty
    if not corps:
        defaults = [
            ("Tata Consultancy Services (TCS Health)", "TCS-CORP", "Rajesh Varma", "rajesh.v@tcs.com", "+91 98110 44552", "07AAACT0001Z1Z0", 500000.0, 42500.0),
            ("Infosys Annual Health Program", "INFY-CORP", "Priya Nair", "health.desk@infosys.com", "+91 98220 77881", "07AAACI1234F1Z5", 350000.0, 18000.0),
            ("HDFC Standard Life Insurance TPA", "HDFC-TPA", "Amit Saxena", "claims@hdfclife.com", "+91 98330 99112", "07AAACH5566G1Z2", 750000.0, 125000.0),
        ]
        for name, code, contact, email, phone, gstin, cred_limit, curr_cred in defaults:
            c = CorporateAccount(
                id=str(uuid.uuid4()),
                tenant_id=tenant_ctx.tenant_id,
                name=name,
                code=code,
                contact_person=contact,
                email=email,
                phone=phone,
                gstin=gstin,
                credit_limit=Decimal(str(cred_limit)),
                current_credit=Decimal(str(curr_cred)),
                billing_cycle="MONTHLY",
                is_active=True,
                created_at=datetime.utcnow(),
            )
            db.add(c)
        db.commit()
        corps = (
            db.query(CorporateAccount)
            .filter(CorporateAccount.tenant_id == tenant_ctx.tenant_id, CorporateAccount.is_active == True)  # noqa: E712
            .order_by(CorporateAccount.name.asc())
            .all()
        )

    out = []
    for c in corps:
        available_credit = float(c.credit_limit) - float(c.current_credit)
        out.append({
            "id": c.id,
            "name": c.name,
            "code": c.code,
            "contact_person": c.contact_person,
            "email": c.email,
            "phone": c.phone,
            "gstin": c.gstin,
            "credit_limit": float(c.credit_limit),
            "current_credit": float(c.current_credit),
            "available_credit": available_credit,
            "billing_cycle": c.billing_cycle,
        })
    return out


@router.post("", status_code=status.HTTP_201_CREATED)
def create_corporate_account(
    payload: CorporateAccountCreate,
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    existing = (
        db.query(CorporateAccount)
        .filter(CorporateAccount.tenant_id == tenant_ctx.tenant_id, CorporateAccount.code == payload.code.upper())
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Corporate client code already exists")

    corp = CorporateAccount(
        id=str(uuid.uuid4()),
        tenant_id=tenant_ctx.tenant_id,
        name=payload.name,
        code=payload.code.upper(),
        contact_person=payload.contact_person,
        email=payload.email,
        phone=payload.phone,
        gstin=payload.gstin,
        address=payload.address,
        credit_limit=Decimal(str(payload.credit_limit)),
        current_credit=Decimal("0.0"),
        billing_cycle=payload.billing_cycle.upper(),
        is_active=True,
        created_at=datetime.utcnow(),
    )
    db.add(corp)
    db.commit()
    db.refresh(corp)
    return {"id": corp.id, "name": corp.name, "code": corp.code, "message": "Corporate account created successfully"}


@router.get("/{corporate_id}/price-list")
def get_corporate_price_list(
    corporate_id: str,
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    corp = (
        db.query(CorporateAccount)
        .filter(CorporateAccount.tenant_id == tenant_ctx.tenant_id, CorporateAccount.id == corporate_id)
        .first()
    )
    if not corp:
        raise HTTPException(status_code=404, detail="Corporate account not found")

    items = db.query(CorporatePriceList).filter(CorporatePriceList.corporate_id == corporate_id).all()
    out = []
    for it in items:
        test = db.query(Test).filter(Test.id == it.test_id).first()
        out.append({
            "id": it.id,
            "test_id": it.test_id,
            "test_code": test.code if test else "UNKNOWN",
            "test_name": test.name if test else "Unknown Test",
            "base_price": float(test.base_price) if test else 0.0,
            "special_rate": float(it.special_rate) if it.special_rate else None,
            "discount_pct": float(it.discount_pct) if it.discount_pct else None,
        })
    return out


@router.post("/{corporate_id}/price-list")
def set_corporate_special_rate(
    corporate_id: str,
    payload: CorporatePriceItemSet,
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    existing = (
        db.query(CorporatePriceList)
        .filter(CorporatePriceList.corporate_id == corporate_id, CorporatePriceList.test_id == payload.test_id)
        .first()
    )
    if existing:
        if payload.special_rate is not None:
            existing.special_rate = Decimal(str(payload.special_rate))
        if payload.discount_pct is not None:
            existing.discount_pct = Decimal(str(payload.discount_pct))
        db.commit()
        return {"message": "Corporate price updated"}
    else:
        new_item = CorporatePriceList(
            id=str(uuid.uuid4()),
            tenant_id=tenant_ctx.tenant_id,
            corporate_id=corporate_id,
            test_id=payload.test_id,
            special_rate=Decimal(str(payload.special_rate)) if payload.special_rate is not None else None,
            discount_pct=Decimal(str(payload.discount_pct)) if payload.discount_pct is not None else None,
            created_at=datetime.utcnow(),
        )
        db.add(new_item)
        db.commit()
        return {"message": "Corporate price added"}


@router.post("/{corporate_id}/invoices", status_code=status.HTTP_201_CREATED)
def generate_corporate_invoice(
    corporate_id: str,
    payload: CorporateInvoiceCreate,
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    corp = (
        db.query(CorporateAccount)
        .filter(CorporateAccount.tenant_id == tenant_ctx.tenant_id, CorporateAccount.id == corporate_id)
        .first()
    )
    if not corp:
        raise HTTPException(status_code=404, detail="Corporate account not found")

    inv_num = f"CORP-INV-{datetime.utcnow().strftime('%y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
    due_date = datetime.utcnow() + timedelta(days=payload.due_days)

    invoice = CorporateInvoice(
        id=str(uuid.uuid4()),
        tenant_id=tenant_ctx.tenant_id,
        corporate_id=corporate_id,
        invoice_number=inv_num,
        period_start=payload.period_start,
        period_end=payload.period_end,
        total_amount=Decimal(str(payload.total_amount)),
        paid_amount=Decimal("0.0"),
        status="ISSUED",
        due_date=due_date,
        issued_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )
    db.add(invoice)

    # Increase corporate current credit
    corp.current_credit += Decimal(str(payload.total_amount))

    db.commit()
    db.refresh(invoice)
    return {
        "invoice_id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "total_amount": float(invoice.total_amount),
        "due_date": invoice.due_date.strftime("%Y-%m-%d"),
        "message": "Corporate monthly invoice generated and issued",
    }

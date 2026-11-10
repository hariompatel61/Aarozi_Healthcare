"""Expenses, Petty Cash, and Vendor Management API router."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.expenses import Expense, ExpenseCategory, Vendor
from app.models.core import Tenant, Branch
from app.security.tenant_guard import get_tenant_context, TenantContext

router = APIRouter(prefix="/expenses", tags=["expenses"])


class ExpenseCategoryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    code: str = Field(..., min_length=2, max_length=50)


class VendorCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    contact_person: str | None = None
    phone: str | None = None
    email: str | None = None
    gstin: str | None = None
    address: str | None = None


class ExpenseCreate(BaseModel):
    branch_id: str | None = None
    category_id: str
    vendor_id: str | None = None
    amount: float = Field(..., gt=0)
    payment_mode: str = "CASH"  # CASH, UPI, BANK_TRANSFER, CHEQUE
    reference_no: str | None = None
    expense_date: datetime | None = None
    description: str = Field(..., min_length=3)
    receipt_attachment: str | None = None


@router.get("/categories")
def list_categories(
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    cats = (
        db.query(ExpenseCategory)
        .filter(ExpenseCategory.tenant_id == tenant_ctx.tenant_id, ExpenseCategory.is_active == True)  # noqa: E712
        .order_by(ExpenseCategory.name.asc())
        .all()
    )
    # If no categories exist, auto-seed defaults for this tenant
    if not cats:
        defaults = [
            ("Reagents & Consumables", "REAGENTS"),
            ("Electricity & Utilities", "UTILITIES"),
            ("Courier & Logistics", "COURIER"),
            ("Staff Refreshments & Petty Cash", "PETTY_CASH"),
            ("Equipment Maintenance & AMC", "EQUIP_MAINT"),
            ("Office Stationery & Printing", "STATIONERY"),
            ("Rent & Facility", "FACILITY_RENT"),
        ]
        for name, code in defaults:
            c = ExpenseCategory(
                id=str(uuid.uuid4()),
                tenant_id=tenant_ctx.tenant_id,
                name=name,
                code=code,
                is_active=True,
            )
            db.add(c)
        db.commit()
        cats = (
            db.query(ExpenseCategory)
            .filter(ExpenseCategory.tenant_id == tenant_ctx.tenant_id, ExpenseCategory.is_active == True)  # noqa: E712
            .order_by(ExpenseCategory.name.asc())
            .all()
        )

    return [{"id": c.id, "name": c.name, "code": c.code, "is_active": c.is_active} for c in cats]


@router.post("/categories", status_code=status.HTTP_201_CREATED)
def create_category(
    payload: ExpenseCategoryCreate,
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    existing = (
        db.query(ExpenseCategory)
        .filter(ExpenseCategory.tenant_id == tenant_ctx.tenant_id, ExpenseCategory.code == payload.code.upper())
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Expense category code already exists")

    cat = ExpenseCategory(
        id=str(uuid.uuid4()),
        tenant_id=tenant_ctx.tenant_id,
        name=payload.name,
        code=payload.code.upper(),
        is_active=True,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return {"id": cat.id, "name": cat.name, "code": cat.code, "message": "Category created successfully"}


@router.get("/vendors")
def list_vendors(
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    vendors = (
        db.query(Vendor)
        .filter(Vendor.tenant_id == tenant_ctx.tenant_id, Vendor.is_active == True)  # noqa: E712
        .order_by(Vendor.name.asc())
        .all()
    )
    return [
        {
            "id": v.id,
            "name": v.name,
            "contact_person": v.contact_person,
            "phone": v.phone,
            "email": v.email,
            "gstin": v.gstin,
            "address": v.address,
        }
        for v in vendors
    ]


@router.post("/vendors", status_code=status.HTTP_201_CREATED)
def create_vendor(
    payload: VendorCreate,
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    v = Vendor(
        id=str(uuid.uuid4()),
        tenant_id=tenant_ctx.tenant_id,
        name=payload.name,
        contact_person=payload.contact_person,
        phone=payload.phone,
        email=payload.email,
        gstin=payload.gstin,
        address=payload.address,
        is_active=True,
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return {"id": v.id, "name": v.name, "message": "Vendor created successfully"}


@router.get("")
def list_expenses(
    category_id: str | None = None,
    vendor_id: str | None = None,
    payment_mode: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    query = db.query(Expense).filter(Expense.tenant_id == tenant_ctx.tenant_id)
    if category_id:
        query = query.filter(Expense.category_id == category_id)
    if vendor_id:
        query = query.filter(Expense.vendor_id == vendor_id)
    if payment_mode:
        query = query.filter(Expense.payment_mode == payment_mode.upper())

    records = query.order_by(Expense.expense_date.desc()).limit(limit).all()
    out = []
    for r in records:
        out.append({
            "id": r.id,
            "branch_id": r.branch_id,
            "category_id": r.category_id,
            "category_name": r.category.name if r.category else "Uncategorized",
            "vendor_id": r.vendor_id,
            "vendor_name": r.vendor.name if r.vendor else None,
            "amount": float(r.amount),
            "payment_mode": r.payment_mode,
            "reference_no": r.reference_no,
            "expense_date": r.expense_date.isoformat(),
            "description": r.description,
            "receipt_attachment": r.receipt_attachment,
        })
    return out


@router.post("", status_code=status.HTTP_201_CREATED)
def record_expense(
    payload: ExpenseCreate,
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    # Resolve default branch if not provided
    branch_id = payload.branch_id
    if not branch_id:
        b = db.query(Branch).filter(Branch.tenant_id == tenant_ctx.tenant_id).first()
        branch_id = b.id if b else "default-branch"

    cat = (
        db.query(ExpenseCategory)
        .filter(ExpenseCategory.tenant_id == tenant_ctx.tenant_id, ExpenseCategory.id == payload.category_id)
        .first()
    )
    if not cat:
        raise HTTPException(status_code=400, detail="Invalid expense category ID")

    expense = Expense(
        id=str(uuid.uuid4()),
        tenant_id=tenant_ctx.tenant_id,
        branch_id=branch_id,
        category_id=payload.category_id,
        vendor_id=payload.vendor_id,
        amount=Decimal(str(payload.amount)),
        payment_mode=payload.payment_mode.upper(),
        reference_no=payload.reference_no,
        expense_date=payload.expense_date or datetime.utcnow(),
        description=payload.description,
        receipt_attachment=payload.receipt_attachment,
        created_at=datetime.utcnow(),
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return {
        "id": expense.id,
        "amount": float(expense.amount),
        "payment_mode": expense.payment_mode,
        "message": "Expense recorded successfully",
    }


@router.get("/summary")
def get_expense_summary(
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    total_spent = (
        db.query(func.coalesce(func.sum(Expense.amount), 0))
        .filter(Expense.tenant_id == tenant_ctx.tenant_id)
        .scalar()
    )
    count = (
        db.query(func.count(Expense.id))
        .filter(Expense.tenant_id == tenant_ctx.tenant_id)
        .scalar()
    )

    # Mode breakdown
    modes = (
        db.query(Expense.payment_mode, func.sum(Expense.amount))
        .filter(Expense.tenant_id == tenant_ctx.tenant_id)
        .group_by(Expense.payment_mode)
        .all()
    )

    return {
        "total_expense_amount": float(total_spent or 0),
        "total_expense_count": count or 0,
        "payment_modes": {m: float(amt or 0) for m, amt in modes},
    }

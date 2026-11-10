"""Laboratory Reagents, Consumables, and Stock Tracking API router."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.inventory import InventoryItem, ReagentLot, StockMovement
from app.models.core import Branch
from app.security.tenant_guard import get_tenant_context, TenantContext

router = APIRouter(prefix="/inventory", tags=["inventory"])


class InventoryItemCreate(BaseModel):
    branch_id: str | None = None
    name: str = Field(..., min_length=2, max_length=255)
    code: str = Field(..., min_length=2, max_length=64)
    category: str = "REAGENT"  # REAGENT, CONSUMABLE, KIT, CONTROL
    unit: str = "TESTS"  # ML, TESTS, VIAL, BOX
    min_stock_alert: float = 10.0
    initial_stock: float = 0.0
    unit_cost: float = 0.0
    storage_conditions: str | None = "2-8°C"


class ReceiveLotCreate(BaseModel):
    item_id: str
    lot_number: str = Field(..., min_length=2)
    expiry_date: datetime
    quantity: float = Field(..., gt=0)


class ConsumeStockCreate(BaseModel):
    item_id: str
    lot_id: str | None = None
    movement_type: str = "USAGE_PER_TEST"  # USAGE_PER_TEST, ADJUSTMENT, WASTAGE, RETURN
    quantity: float = Field(..., gt=0)
    notes: str | None = None


@router.get("/items")
def list_inventory_items(
    category: str | None = None,
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    query = db.query(InventoryItem).filter(InventoryItem.tenant_id == tenant_ctx.tenant_id, InventoryItem.is_active == True)  # noqa: E712
    if category:
        query = query.filter(InventoryItem.category == category.upper())

    items = query.order_by(InventoryItem.name.asc()).all()

    # Seed default common reagents if catalog is empty
    if not items:
        b = db.query(Branch).filter(Branch.tenant_id == tenant_ctx.tenant_id).first()
        branch_id = b.id if b else "default-branch"

        defaults = [
            ("CBC Diluent Reagent (20L)", "CBC-DIL-01", "REAGENT", "TESTS", 100.0, 500.0, 1500.0, "Room Temp"),
            ("CBC Lyse Reagent (500ml)", "CBC-LYS-01", "REAGENT", "TESTS", 50.0, 300.0, 2400.0, "Room Temp"),
            ("Glucose GOD-POD Biochemistry Reagent", "BIO-GLU-01", "REAGENT", "TESTS", 100.0, 800.0, 950.0, "2-8°C"),
            ("Serum Creatinine Jaffe Reagent Kit", "BIO-CREAT-01", "REAGENT", "TESTS", 50.0, 400.0, 1100.0, "2-8°C"),
            ("SGPT/ALT Kinetic Liquid Reagent", "BIO-ALT-01", "REAGENT", "TESTS", 40.0, 250.0, 1850.0, "2-8°C"),
            ("EDTA K2 Vacuum Blood Collection Tubes (Purple)", "VAC-EDTA-01", "CONSUMABLE", "PIECES", 200.0, 1200.0, 4.5, "Room Temp"),
            ("Serum Separator Clot Activator Tubes (Yellow)", "VAC-SST-01", "CONSUMABLE", "PIECES", 200.0, 950.0, 5.0, "Room Temp"),
            ("Sterile Alcohol Prep Swabs (Box of 100)", "SWAB-ALC-01", "CONSUMABLE", "BOX", 5.0, 25.0, 85.0, "Room Temp"),
        ]
        for name, code, cat, unit, min_s, curr_s, cost, cond in defaults:
            it = InventoryItem(
                id=str(uuid.uuid4()),
                tenant_id=tenant_ctx.tenant_id,
                branch_id=branch_id,
                name=name,
                code=code,
                category=cat,
                unit=unit,
                min_stock_alert=Decimal(str(min_s)),
                current_stock=Decimal(str(curr_s)),
                unit_cost=Decimal(str(cost)),
                storage_conditions=cond,
                is_active=True,
                created_at=datetime.utcnow(),
            )
            db.add(it)
        db.commit()
        items = query.order_by(InventoryItem.name.asc()).all()

    out = []
    for it in items:
        is_low = float(it.current_stock) <= float(it.min_stock_alert)
        out.append({
            "id": it.id,
            "branch_id": it.branch_id,
            "name": it.name,
            "code": it.code,
            "category": it.category,
            "unit": it.unit,
            "min_stock_alert": float(it.min_stock_alert),
            "current_stock": float(it.current_stock),
            "unit_cost": float(it.unit_cost),
            "storage_conditions": it.storage_conditions,
            "is_low_stock": is_low,
        })
    return out


@router.post("/items", status_code=status.HTTP_201_CREATED)
def create_inventory_item(
    payload: InventoryItemCreate,
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    branch_id = payload.branch_id
    if not branch_id:
        b = db.query(Branch).filter(Branch.tenant_id == tenant_ctx.tenant_id).first()
        branch_id = b.id if b else "default-branch"

    existing = (
        db.query(InventoryItem)
        .filter(InventoryItem.tenant_id == tenant_ctx.tenant_id, InventoryItem.branch_id == branch_id, InventoryItem.code == payload.code.upper())
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Inventory item code already exists for this branch")

    it = InventoryItem(
        id=str(uuid.uuid4()),
        tenant_id=tenant_ctx.tenant_id,
        branch_id=branch_id,
        name=payload.name,
        code=payload.code.upper(),
        category=payload.category.upper(),
        unit=payload.unit.upper(),
        min_stock_alert=Decimal(str(payload.min_stock_alert)),
        current_stock=Decimal(str(payload.initial_stock)),
        unit_cost=Decimal(str(payload.unit_cost)),
        storage_conditions=payload.storage_conditions,
        is_active=True,
        created_at=datetime.utcnow(),
    )
    db.add(it)
    db.commit()
    db.refresh(it)
    return {"id": it.id, "name": it.name, "code": it.code, "message": "Item registered successfully"}


@router.post("/lots", status_code=status.HTTP_201_CREATED)
def receive_reagent_lot(
    payload: ReceiveLotCreate,
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    it = (
        db.query(InventoryItem)
        .filter(InventoryItem.tenant_id == tenant_ctx.tenant_id, InventoryItem.id == payload.item_id)
        .first()
    )
    if not it:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    lot = ReagentLot(
        id=str(uuid.uuid4()),
        tenant_id=tenant_ctx.tenant_id,
        item_id=payload.item_id,
        lot_number=payload.lot_number,
        expiry_date=payload.expiry_date,
        quantity_received=Decimal(str(payload.quantity)),
        quantity_remaining=Decimal(str(payload.quantity)),
        received_date=datetime.utcnow(),
        is_active=True,
        created_at=datetime.utcnow(),
    )
    db.add(lot)

    # Increase current stock on item
    it.current_stock += Decimal(str(payload.quantity))

    # Log movement
    mov = StockMovement(
        id=str(uuid.uuid4()),
        tenant_id=tenant_ctx.tenant_id,
        branch_id=it.branch_id,
        item_id=it.id,
        lot_id=lot.id,
        movement_type="PURCHASE",
        quantity=Decimal(str(payload.quantity)),
        notes=f"Received Lot #{payload.lot_number}",
        timestamp=datetime.utcnow(),
    )
    db.add(mov)

    db.commit()
    db.refresh(lot)
    return {
        "id": lot.id,
        "lot_number": lot.lot_number,
        "quantity_remaining": float(lot.quantity_remaining),
        "total_item_stock": float(it.current_stock),
        "message": "Lot received and added to stock successfully",
    }


@router.post("/consume")
def consume_stock(
    payload: ConsumeStockCreate,
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    it = (
        db.query(InventoryItem)
        .filter(InventoryItem.tenant_id == tenant_ctx.tenant_id, InventoryItem.id == payload.item_id)
        .first()
    )
    if not it:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    deduct = Decimal(str(payload.quantity))
    if it.current_stock < deduct:
        raise HTTPException(status_code=400, detail=f"Insufficient stock. Available: {float(it.current_stock)}")

    it.current_stock -= deduct

    mov = StockMovement(
        id=str(uuid.uuid4()),
        tenant_id=tenant_ctx.tenant_id,
        branch_id=it.branch_id,
        item_id=it.id,
        lot_id=payload.lot_id,
        movement_type=payload.movement_type.upper(),
        quantity=deduct,
        notes=payload.notes,
        timestamp=datetime.utcnow(),
    )
    db.add(mov)
    db.commit()
    db.refresh(it)
    return {
        "id": it.id,
        "current_stock": float(it.current_stock),
        "message": f"Recorded consumption of {payload.quantity} {it.unit}",
    }


@router.get("/alerts")
def get_inventory_alerts(
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    low_stock = (
        db.query(InventoryItem)
        .filter(InventoryItem.tenant_id == tenant_ctx.tenant_id, InventoryItem.current_stock <= InventoryItem.min_stock_alert)
        .all()
    )

    one_month = datetime.utcnow() + timedelta(days=30)
    expiring_soon = (
        db.query(ReagentLot)
        .join(InventoryItem)
        .filter(
            ReagentLot.tenant_id == tenant_ctx.tenant_id,
            ReagentLot.quantity_remaining > 0,
            ReagentLot.expiry_date <= one_month,
        )
        .all()
    )

    return {
        "low_stock_items": [
            {
                "id": i.id,
                "name": i.name,
                "code": i.code,
                "current_stock": float(i.current_stock),
                "min_alert": float(i.min_stock_alert),
                "unit": i.unit,
            }
            for i in low_stock
        ],
        "expiring_lots": [
            {
                "id": lot.id,
                "item_name": lot.item.name if lot.item else "Unknown",
                "lot_number": lot.lot_number,
                "expiry_date": lot.expiry_date.strftime("%Y-%m-%d"),
                "remaining": float(lot.quantity_remaining),
            }
            for lot in expiring_soon
        ],
    }

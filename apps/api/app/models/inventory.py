"""Laboratory Reagents, Consumables, and Stock Tracking relational models."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id: Mapped[str] = mapped_column(String(36), ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    department_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="REAGENT")  # REAGENT, CONSUMABLE, KIT, CONTROL
    unit: Mapped[str] = mapped_column(String(30), nullable=False, default="TESTS")  # ML, TESTS, VIAL, BOX, PIECES
    
    min_stock_alert: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=10.0)
    current_stock: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)
    storage_conditions: Mapped[str | None] = mapped_column(String(100), nullable=True)  # e.g. "2-8°C", "Room Temp"
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    lots: Mapped[list[ReagentLot]] = relationship("ReagentLot", back_populates="item", cascade="all, delete-orphan")
    movements: Mapped[list[StockMovement]] = relationship("StockMovement", back_populates="item")

    __table_args__ = (
        Index("ix_inventory_tenant_branch_code", "tenant_id", "branch_id", "code", unique=True),
    )


class ReagentLot(Base):
    __tablename__ = "reagent_lots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id: Mapped[str] = mapped_column(String(36), ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False, index=True)

    lot_number: Mapped[str] = mapped_column(String(100), nullable=False)
    expiry_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    quantity_received: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    quantity_remaining: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    received_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    item: Mapped[InventoryItem] = relationship("InventoryItem", back_populates="lots")


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id: Mapped[str] = mapped_column(String(36), ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id: Mapped[str] = mapped_column(String(36), ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False, index=True)
    lot_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("reagent_lots.id", ondelete="SET NULL"), nullable=True)

    movement_type: Mapped[str] = mapped_column(String(40), nullable=False)  # PURCHASE, USAGE_PER_TEST, ADJUSTMENT, WASTAGE, RETURN
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    reference_test_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    item: Mapped[InventoryItem] = relationship("InventoryItem", back_populates="movements")

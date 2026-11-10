"""Corporate Client Management and B2B Billing relational models."""
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


class CorporateAccount(Base):
    __tablename__ = "corporate_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    contact_person: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    gstin: Mapped[str | None] = mapped_column(String(30), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    credit_limit: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=100000.0)
    current_credit: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0.0)
    billing_cycle: Mapped[str] = mapped_column(String(30), nullable=False, default="MONTHLY")  # MONTHLY, BIWEEKLY, PER_ORDER
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    price_lists: Mapped[list[CorporatePriceList]] = relationship("CorporatePriceList", back_populates="corporate", cascade="all, delete-orphan")
    invoices: Mapped[list[CorporateInvoice]] = relationship("CorporateInvoice", back_populates="corporate")

    __table_args__ = (
        Index("ix_corporate_accounts_tenant_code", "tenant_id", "code", unique=True),
    )


class CorporatePriceList(Base):
    __tablename__ = "corporate_price_lists"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    corporate_id: Mapped[str] = mapped_column(String(36), ForeignKey("corporate_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    test_id: Mapped[str] = mapped_column(String(36), ForeignKey("tests.id", ondelete="CASCADE"), nullable=False, index=True)

    special_rate: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    discount_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    corporate: Mapped[CorporateAccount] = relationship("CorporateAccount", back_populates="price_lists")

    __table_args__ = (
        Index("ix_corporate_test_unique", "corporate_id", "test_id", unique=True),
    )


class CorporateInvoice(Base):
    __tablename__ = "corporate_invoices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    corporate_id: Mapped[str] = mapped_column(String(36), ForeignKey("corporate_accounts.id", ondelete="CASCADE"), nullable=False, index=True)

    invoice_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="DRAFT")  # DRAFT, ISSUED, PARTIAL, PAID, OVERDUE
    
    due_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    corporate: Mapped[CorporateAccount] = relationship("CorporateAccount", back_populates="invoices")


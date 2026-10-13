"""Billing and Pricing ORM models."""
from __future__ import annotations

import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Index,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class ReferralPartner(Base):
    """Referral partner entity (e.g., doctor, hospital, external lab, collection centre, corporate account)."""
    __tablename__ = "referral_partners"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    partner_type: Mapped[str] = mapped_column(String(50), nullable=False)  # doctor, hospital, lab, collection_centre, corporate
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")  # active, inactive
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    rules: Mapped[list[ReferralRule]] = relationship(
        "ReferralRule",
        back_populates="partner",
        cascade="all, delete-orphan",
    )
    commission_ledgers: Mapped[list[CommissionLedger]] = relationship(
        "CommissionLedger",
        back_populates="partner",
        cascade="all, delete-orphan",
    )


class ReferralRule(Base):
    """Referral rule with priority and discount/commission settings."""
    __tablename__ = "referral_rules"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    partner_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("referral_partners.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scope_type: Mapped[str] = mapped_column(String(50), nullable=False, default="all")  # all, test, department, package, profile
    scope_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    patient_discount_pct: Mapped[float] = mapped_column(Numeric(7, 4), nullable=False, default=0.0)
    commission_pct: Mapped[float] = mapped_column(Numeric(7, 4), nullable=False, default=0.0)
    commission_fixed: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    priority: Mapped[int] = mapped_column(nullable=False, default=100)  # lower number = higher precedence
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    partner: Mapped[ReferralPartner] = relationship("ReferralPartner", back_populates="rules")



class PriceList(Base):
    """Price list definition at tenant level with optional branch-level specificity and date validity."""
    __tablename__ = "price_lists"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    branch_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("branches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")  # active, archived, draft
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
    )
    effective_to: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    items: Mapped[list[PriceListItem]] = relationship(
        "PriceListItem",
        back_populates="price_list",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_price_lists_tenant_code"),
    )


class PriceListItem(Base):
    """Specific line item rate/price within a price list for a test, profile, or package."""
    __tablename__ = "price_list_items"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    price_list_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("price_lists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_type: Mapped[str] = mapped_column(String(30), nullable=False)  # test, profile, package
    item_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    rate: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0.0)
    min_rate: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    max_discount_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0.0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    price_list: Mapped[PriceList] = relationship("PriceList", back_populates="items")

    __table_args__ = (
        UniqueConstraint(
            "price_list_id",
            "item_type",
            "item_id",
            name="uq_price_list_item_target",
        ),
    )



class Invoice(Base):
    """Financial invoice document representing billed services, orders, and products."""
    __tablename__ = "invoices"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    branch_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("branches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    patient_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("patients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    order_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    referral_partner_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("referral_partners.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    invoice_no: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="issued",
    )  # draft, issued, part_paid, paid, cancelled, refund_pending, refunded
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    subtotal: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0.0)
    discount_total: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0.0)
    tax_total: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0.0)
    grand_total: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0.0)
    paid_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0.0)
    refund_total: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0.0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    items: Mapped[list[InvoiceItem]] = relationship(
        "InvoiceItem",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )

    payments: Mapped[list[Payment]] = relationship(
        "Payment",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )

    refunds: Mapped[list[Refund]] = relationship(
        "Refund",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )
    commission_ledgers: Mapped[list[CommissionLedger]] = relationship(
        "CommissionLedger",
        back_populates="invoice",
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "invoice_no", name="uq_invoices_tenant_invoice_no"),
    )


class InvoiceItem(Base):
    """Line item within an invoice with rate, discount, and tax auditability."""
    __tablename__ = "invoice_items"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    invoice_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    order_item_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("order_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    item_type: Mapped[str] = mapped_column(String(30), nullable=False, default="test")  # test, profile, package, fee, manual
    item_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    qty: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False, default=1.0)
    unit_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0.0)
    discount_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0.0)
    discount_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0.0)
    tax_rate_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0.0)
    tax_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0.0)
    line_total: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    invoice: Mapped[Invoice] = relationship("Invoice", back_populates="items")


class Payment(Base):
    """Financial payment transaction recorded against an invoice."""
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    invoice_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("invoices.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    method: Mapped[str] = mapped_column(String(50), nullable=False)  # cash, card, upi, bank_transfer, cheque, online
    provider_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    receipt_no: Mapped[str | None] = mapped_column(String(64), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="success")  # success, pending, failed
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    invoice: Mapped[Invoice] = relationship("Invoice", back_populates="payments")
    refunds: Mapped[list[Refund]] = relationship("Refund", back_populates="payment")

    __table_args__ = (
        UniqueConstraint("tenant_id", "receipt_no", name="uq_payments_tenant_receipt_no"),
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_payments_tenant_idempotency_key"),
        Index("idx_payments_invoice", "invoice_id", "received_at"),
    )



class Refund(Base):
    """Financial refund transaction recorded against an invoice / payment."""
    __tablename__ = "refunds"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    invoice_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("invoices.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    payment_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("payments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    refund_no: Mapped[str] = mapped_column(String(64), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    method: Mapped[str] = mapped_column(String(50), nullable=False)  # cash, card, upi, bank_transfer, original_payment
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="completed")  # pending, completed, failed
    provider_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    processed_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    invoice: Mapped[Invoice] = relationship("Invoice", back_populates="refunds")
    payment: Mapped[Payment | None] = relationship("Payment", back_populates="refunds")

    __table_args__ = (
        UniqueConstraint("tenant_id", "refund_no", name="uq_refunds_tenant_refund_no"),
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_refunds_tenant_idempotency_key"),
        Index("idx_refunds_invoice", "invoice_id", "created_at"),
    )


class CommissionLedger(Base):
    """Calculated referral partner entitlement and settlement ledger."""
    __tablename__ = "commission_ledger"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    referral_partner_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("referral_partners.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    invoice_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
    )  # pending, settled, cancelled
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    settled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    settlement_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    settled_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    breakdown_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    partner: Mapped[ReferralPartner] = relationship("ReferralPartner", back_populates="commission_ledgers")
    invoice: Mapped[Invoice | None] = relationship("Invoice", back_populates="commission_ledgers")

    __table_args__ = (
        Index("ix_commission_ledger_tenant_status", "tenant_id", "status"),
        Index("ix_commission_ledger_partner_status", "tenant_id", "referral_partner_id", "status"),
    )





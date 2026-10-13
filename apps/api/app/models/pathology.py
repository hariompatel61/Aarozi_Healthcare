from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Test(Base):
    __tablename__ = "tests"

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
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Specimen & Collection
    specimen_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    container_type: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Method & Technical
    method: Mapped[str | None] = mapped_column(String(100), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    decimal_precision: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    precision: Mapped[int | None] = mapped_column(Integer, nullable=True)
    calculation_rule: Mapped[str | None] = mapped_column(Text, nullable=True)
    calculation_formula: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_calculated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    analyzer_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    loinc_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    department_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Status & Active Versioning
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active", index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    effective_to: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    superseded_by_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("tests.id", ondelete="SET NULL"),
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

    reference_ranges: Mapped[list[TestReferenceRange]] = relationship(
        "TestReferenceRange",
        back_populates="test",
        cascade="all, delete-orphan",
    )

    superseded_by: Mapped[Test | None] = relationship(
        "Test",
        remote_side=[id],
        foreign_keys=[superseded_by_id],
        post_update=True,
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "code", "version", name="uq_tests_tenant_code_version"),
        Index("ix_tests_tenant_code", "tenant_id", "code"),
        Index("ix_tests_tenant_status", "tenant_id", "status"),
    )


class TestReferenceRange(Base):
    __tablename__ = "test_reference_ranges"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    test_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sex: Mapped[str] = mapped_column(String(20), nullable=False, default="all")  # all, male, female, other
    age_min: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    age_max: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    age_unit: Mapped[str] = mapped_column(String(20), nullable=False, default="years")  # years, months, days
    context: Mapped[str | None] = mapped_column(String(100), nullable=True)  # fasting, postprandial, random, trimester_1, etc.
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    low_value: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    high_value: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    critical_low: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    critical_high: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    text_range: Mapped[str | None] = mapped_column(Text, nullable=True)
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    test: Mapped[Test] = relationship("Test", back_populates="reference_ranges")

    __table_args__ = (
        Index("ix_test_ref_ranges_test_id", "test_id"),
        Index("ix_test_ref_ranges_lookup", "test_id", "sex", "context"),
    )



class Profile(Base):
    __tablename__ = "profiles"

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
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    department_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active", index=True)
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

    items: Mapped[list[ProfileItem]] = relationship(
        "ProfileItem",
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="ProfileItem.sort_order",
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_profiles_tenant_code"),
        Index("ix_profiles_tenant_code", "tenant_id", "code"),
        Index("ix_profiles_tenant_status", "tenant_id", "status"),
    )


class ProfileItem(Base):
    __tablename__ = "profile_items"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    profile_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    test_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tests.id", ondelete="CASCADE"),
        nullable=False,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    profile: Mapped[Profile] = relationship("Profile", back_populates="items")
    test: Mapped[Test] = relationship("Test")

    __table_args__ = (
        UniqueConstraint("profile_id", "test_id", name="uq_profile_items_profile_test"),
        Index("ix_profile_items_profile_id", "profile_id"),
        Index("ix_profile_items_test_id", "test_id"),
    )


class Package(Base):
    __tablename__ = "packages"

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
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active", index=True)
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

    items: Mapped[list[PackageItem]] = relationship(
        "PackageItem",
        back_populates="package",
        cascade="all, delete-orphan",
        order_by="PackageItem.sort_order",
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_packages_tenant_code"),
        Index("ix_packages_tenant_code", "tenant_id", "code"),
        Index("ix_packages_tenant_status", "tenant_id", "status"),
    )


class PackageItem(Base):
    __tablename__ = "package_items"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    package_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("packages.id", ondelete="CASCADE"),
        nullable=False,
    )
    test_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("tests.id", ondelete="CASCADE"),
        nullable=True,
    )
    profile_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    package: Mapped[Package] = relationship("Package", back_populates="items")
    test: Mapped[Test | None] = relationship("Test")
    profile: Mapped[Profile | None] = relationship("Profile")

    __table_args__ = (
        Index("ix_package_items_package_id", "package_id"),
        Index("ix_package_items_test_id", "test_id"),
        Index("ix_package_items_profile_id", "profile_id"),
    )


class Order(Base):
    __tablename__ = "orders"

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
    order_no: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft", index=True)
    referral_partner_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    ordered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    created_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancelled_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    items: Mapped[list[OrderItem]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "order_no", name="uq_orders_tenant_order_no"),
        Index("ix_orders_tenant_order_no", "tenant_id", "order_no"),
        Index("ix_orders_tenant_status", "tenant_id", "status"),
        Index("ix_orders_tenant_patient", "tenant_id", "patient_id"),
        Index("ix_orders_tenant_branch_status", "tenant_id", "branch_id", "status"),
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    order_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    test_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tests.id", ondelete="RESTRICT"),
        nullable=False,
    )
    profile_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    package_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")
    price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0.0)
    discount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0.0)
    tax: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0.0)
    final_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0.0)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    order: Mapped[Order] = relationship("Order", back_populates="items")
    test: Mapped[Test] = relationship("Test")
    samples: Mapped[list[Sample]] = relationship(
        "Sample",
        back_populates="order_item",
        cascade="all, delete-orphan",
    )
    results: Mapped[list[Result]] = relationship(
        "Result",
        back_populates="order_item",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_order_items_order_id", "order_id"),
        Index("ix_order_items_test_id", "test_id"),
        Index("ix_order_items_status", "status"),
    )


class Sample(Base):
    __tablename__ = "samples"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    order_item_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("order_items.id", ondelete="RESTRICT"),
        nullable=False,
    )
    barcode: Mapped[str] = mapped_column(String(64), nullable=False)
    specimen_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    container_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="ordered")

    collected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    collected_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    received_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    accepted_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

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

    order_item: Mapped[OrderItem] = relationship("OrderItem", back_populates="samples")

    __table_args__ = (
        UniqueConstraint("tenant_id", "barcode", name="uq_samples_tenant_barcode"),
        Index("ix_samples_tenant_id", "tenant_id"),
        Index("ix_samples_order_item_id", "order_item_id"),
        Index("ix_samples_barcode", "tenant_id", "barcode"),
        Index("ix_samples_tenant_status", "tenant_id", "status"),
        Index("idx_sample_queue", "tenant_id", "status", "received_at"),
    )



class Result(Base):
    __tablename__ = "results"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    order_item_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("order_items.id", ondelete="RESTRICT"),
        nullable=False,
    )
    sample_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("samples.id", ondelete="SET NULL"),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")  # draft, entered, verified, released, amended

    entered_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    entered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    verified_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    approved_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    amendment_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    amended_from_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("results.id", ondelete="SET NULL"),
        nullable=True,
    )
    signature_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

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

    order_item: Mapped[OrderItem] = relationship("OrderItem", back_populates="results")
    sample: Mapped[Sample | None] = relationship("Sample")
    values: Mapped[list[ResultValue]] = relationship(
        "ResultValue",
        back_populates="result",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("order_item_id", "version", name="uq_results_order_item_version"),
        Index("ix_results_tenant_id", "tenant_id"),
        Index("ix_results_order_item_id", "order_item_id"),
        Index("ix_results_tenant_status", "tenant_id", "status"),
        Index("idx_result_queue", "tenant_id", "status", "updated_at"),
    )


class ResultValue(Base):
    __tablename__ = "result_values"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    result_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("results.id", ondelete="CASCADE"),
        nullable=False,
    )
    analyte_code: Mapped[str] = mapped_column(String(64), nullable=False)
    analyte_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    numeric_value: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_range_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("test_reference_ranges.id", ondelete="SET NULL"),
        nullable=True,
    )
    abnormal_flag: Mapped[str | None] = mapped_column(String(30), nullable=True)  # normal, low, high, critical_low, critical_high, abnormal
    critical_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    result: Mapped[Result] = relationship("Result", back_populates="values")
    reference_range: Mapped[TestReferenceRange | None] = relationship("TestReferenceRange")

    __table_args__ = (
        Index("ix_result_values_result_id", "result_id"),
        Index("ix_result_values_analyte_code", "analyte_code"),
    )




class CriticalAlert(Base):
    __tablename__ = "critical_alerts"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    result_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("results.id", ondelete="CASCADE"),
        nullable=False,
    )
    result_value_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("result_values.id", ondelete="CASCADE"),
        nullable=False,
    )
    patient_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
    )
    order_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    analyte_code: Mapped[str] = mapped_column(String(64), nullable=False)
    flag: Mapped[str] = mapped_column(String(30), nullable=False)  # critical_low, critical_high, critical_abnormal
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending_acknowledgement")  # pending_acknowledgement, acknowledged, escalated
    communicated_to: Mapped[str | None] = mapped_column(String(255), nullable=True)
    acknowledged_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    result: Mapped[Result] = relationship("Result")
    result_value: Mapped[ResultValue] = relationship("ResultValue")

    __table_args__ = (
        Index("ix_critical_alerts_tenant_id", "tenant_id"),
        Index("ix_critical_alerts_status", "tenant_id", "status"),
        Index("ix_critical_alerts_patient_id", "patient_id"),
        Index("ix_critical_alerts_result_id", "result_id"),
    )


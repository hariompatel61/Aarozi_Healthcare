"""Blood Bank & Transfusion Medicine ORM models."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Index,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Donor(Base):
    __tablename__ = "donors"

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
    donor_no: Mapped[str] = mapped_column(String(50), nullable=False)
    patient_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("patients.id", ondelete="SET NULL"),
        nullable=True,
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    sex: Mapped[str] = mapped_column(String(20), nullable=False, default="all")
    blood_group: Mapped[str | None] = mapped_column(String(20), nullable=True)
    mobile: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    national_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    abha_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    last_donation_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_donations: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
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

    deferrals: Mapped[list[DonorDeferral]] = relationship(
        "DonorDeferral",
        back_populates="donor",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "donor_no", name="uq_donors_tenant_donor_no"),
        Index("ix_donors_mobile", "tenant_id", "mobile"),
        Index("ix_donors_blood_group", "tenant_id", "blood_group"),
        Index("ix_donors_status", "tenant_id", "status"),
    )


class DonorDeferral(Base):
    __tablename__ = "donor_deferrals"

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
    donor_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("donors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    deferral_type: Mapped[str] = mapped_column(String(30), nullable=False)  # temporary, permanent
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    deferred_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")  # active, lifted
    lift_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    deferred_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    lifted_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    deferred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    lifted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    donor: Mapped[Donor] = relationship("Donor", back_populates="deferrals")

    __table_args__ = (
        Index("ix_donor_deferrals_status", "donor_id", "status"),
    )

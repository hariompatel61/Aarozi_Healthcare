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
    BigInteger,
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
    screenings: Mapped[list[DonorScreening]] = relationship(
        "DonorScreening",
        back_populates="donor",
        cascade="all, delete-orphan",
    )
    donations: Mapped[list[Donation]] = relationship(
        "Donation",
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



class DonorScreening(Base):
    __tablename__ = "donor_screenings"

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
    screening_no: Mapped[str] = mapped_column(String(50), nullable=False)
    weight_kg: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    blood_pressure_systolic: Mapped[int | None] = mapped_column(Integer, nullable=True)
    blood_pressure_diastolic: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pulse_bpm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    temperature_c: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    hemoglobin_g_dl: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    questionnaire_responses: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="passed")
    eligibility_status: Mapped[str] = mapped_column(String(30), nullable=False, default="eligible")
    deferral_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    deferred_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deferral_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("donor_deferrals.id", ondelete="SET NULL"),
        nullable=True,
    )
    screened_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    screened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
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

    donor: Mapped[Donor] = relationship("Donor", back_populates="screenings")
    deferral: Mapped[DonorDeferral | None] = relationship("DonorDeferral")

    __table_args__ = (
        UniqueConstraint("tenant_id", "screening_no", name="uq_donor_screenings_screening_no"),
        Index("ix_donor_screenings_status", "tenant_id", "status"),
    )


class Donation(Base):
    __tablename__ = "donations"

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
    screening_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("donor_screenings.id", ondelete="SET NULL"),
        nullable=True,
    )
    donation_no: Mapped[str] = mapped_column(String(50), nullable=False)
    donation_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="whole_blood",
    )  # whole_blood, plateletpheresis, etc.
    bag_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="single",
    )  # single, double, triple, quadruple, apheresis
    volume_ml: Mapped[int] = mapped_column(Integer, nullable=False, default=450)
    blood_group: Mapped[str | None] = mapped_column(String(20), nullable=True)
    venipuncture_site: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="completed",
    )  # completed, incomplete, adverse_reaction
    screening_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="passed",
    )
    eligibility_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="eligible",
    )
    deferral_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    collected_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    donated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
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

    donor: Mapped[Donor] = relationship("Donor", back_populates="donations")
    screening: Mapped[DonorScreening | None] = relationship("DonorScreening")
    blood_units: Mapped[list[BloodUnit]] = relationship(
        "BloodUnit",
        back_populates="donation",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "donation_no", name="uq_donations_donation_no"),
        Index("ix_donations_status", "tenant_id", "status"),
    )


class BloodUnit(Base):
    __tablename__ = "blood_units"

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
    donation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("donations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    unit_no: Mapped[str] = mapped_column(String(50), nullable=False)
    component_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # whole_blood, packed_red_cells, fresh_frozen_plasma, platelet_concentrate, cryoprecipitate
    blood_group: Mapped[str | None] = mapped_column(String(20), nullable=True)
    volume_ml: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="collected",
    )  # collected, testing, quarantined, released, reserved, issued, discarded
    storage_location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    expiry_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
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

    donation: Mapped[Donation] = relationship("Donation", back_populates="blood_units")
    movements: Mapped[list[BloodMovement]] = relationship(
        "BloodMovement",
        back_populates="blood_unit",
        cascade="all, delete-orphan",
    )
    tests: Mapped[list[BloodUnitTest]] = relationship(
        "BloodUnitTest",
        back_populates="blood_unit",
        cascade="all, delete-orphan",
    )
    cross_matches: Mapped[list[CrossMatch]] = relationship(
        "CrossMatch",
        back_populates="blood_unit",
        cascade="all, delete-orphan",
    )
    adverse_events: Mapped[list[AdverseEvent]] = relationship(
        "AdverseEvent",
        back_populates="blood_unit",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "unit_no", name="uq_blood_units_unit_no"),
        Index("ix_blood_stock", "tenant_id", "blood_group", "component_type", "status", "expiry_at"),
    )


class BloodMovement(Base):
    __tablename__ = "blood_movements"

    id: Mapped[int] = mapped_column(
        Integer().with_variant(BigInteger, "postgresql"),
        primary_key=True,
        autoincrement=True,
    )
    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    blood_unit_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("blood_units.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    movement_type: Mapped[str] = mapped_column(String(50), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    to_status: Mapped[str] = mapped_column(String(30), nullable=False)
    patient_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("patients.id", ondelete="SET NULL"),
        nullable=True,
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor_user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    blood_unit: Mapped[BloodUnit] = relationship("BloodUnit", back_populates="movements")


class BloodUnitTest(Base):
    __tablename__ = "blood_unit_tests"

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
    blood_unit_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("blood_units.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    test_code: Mapped[str] = mapped_column(String(50), nullable=False)
    result: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    verified_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    blood_unit: Mapped[BloodUnit] = relationship("BloodUnit", back_populates="tests")


class CrossMatch(Base):
    __tablename__ = "cross_matches"

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
    patient_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    blood_unit_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("blood_units.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    compatibility_status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    performed_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    performed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    blood_unit: Mapped[BloodUnit] = relationship("BloodUnit", back_populates="cross_matches")


class AdverseEvent(Base):
    __tablename__ = "adverse_events"

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
    blood_unit_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("blood_units.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    patient_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reaction_type: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(30), nullable=False, default="moderate")
    symptoms: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_taken: Mapped[str | None] = mapped_column(Text, nullable=True)
    reported_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    blood_unit: Mapped[BloodUnit] = relationship("BloodUnit", back_populates="adverse_events")



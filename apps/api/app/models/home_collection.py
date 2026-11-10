"""Home Sample Collection Dispatch and Tracking models."""
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


class HomeCollectionBooking(Base):
    __tablename__ = "home_collection_bookings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id: Mapped[str] = mapped_column(String(36), ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)

    appointment_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    time_slot: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "07:00 AM - 08:00 AM"
    
    address: Mapped[str] = mapped_column(Text, nullable=False)
    landmark: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pincode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    geo_lat: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    geo_lng: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    
    contact_phone: Mapped[str] = mapped_column(String(30), nullable=False)
    alternate_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    
    phlebotomist_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="REQUESTED", index=True)
    # REQUESTED -> SCHEDULED -> OUT_FOR_COLLECTION -> COLLECTED -> ARRIVED_AT_LAB -> CANCELLED
    
    collection_charge: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0.0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    collected_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    arrived_at_lab_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    patient = relationship("Patient")
    order = relationship("Order")
    phlebotomist = relationship("User", foreign_keys=[phlebotomist_id])

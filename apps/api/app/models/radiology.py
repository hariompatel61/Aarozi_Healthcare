"""Radiology and Imaging Investigation relational models."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class RadiologyOrder(Base):
    __tablename__ = "radiology_orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id: Mapped[str] = mapped_column(String(36), ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)

    accession_no: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    modality: Mapped[str] = mapped_column(String(30), nullable=False)  # XRAY, USG, CT, MRI, ECG, ECHO
    procedure_name: Mapped[str] = mapped_column(String(255), nullable=False)
    clinical_history: Mapped[str | None] = mapped_column(Text, nullable=True)
    referring_doctor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="PENDING", index=True)
    # PENDING -> SCAN_COMPLETED -> REPORT_DRAFTED -> FINALIZED -> DELIVERED
    
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    findings: Mapped[list[RadiologyFinding]] = relationship("RadiologyFinding", back_populates="order", cascade="all, delete-orphan")
    patient = relationship("Patient")


class RadiologyFinding(Base):
    __tablename__ = "radiology_findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id: Mapped[str] = mapped_column(String(36), ForeignKey("radiology_orders.id", ondelete="CASCADE"), nullable=False, index=True)

    technique: Mapped[str | None] = mapped_column(Text, nullable=True)
    comparison: Mapped[str | None] = mapped_column(Text, nullable=True)
    findings: Mapped[str] = mapped_column(Text, nullable=False)
    impression: Mapped[str] = mapped_column(Text, nullable=False)
    recommendations: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    radiologist_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="DRAFT")  # DRAFT, FINALIZED, AMENDED
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    order: Mapped[RadiologyOrder] = relationship("RadiologyOrder", back_populates="findings")
    attachments: Mapped[list[RadiologyAttachment]] = relationship("RadiologyAttachment", back_populates="finding", cascade="all, delete-orphan")


class RadiologyAttachment(Base):
    __tablename__ = "radiology_attachments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    finding_id: Mapped[str] = mapped_column(String(36), ForeignKey("radiology_findings.id", ondelete="CASCADE"), nullable=False, index=True)

    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)  # image/jpeg, image/png, application/dicom
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    finding: Mapped[RadiologyFinding] = relationship("RadiologyFinding", back_populates="attachments")


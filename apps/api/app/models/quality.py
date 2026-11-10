"""NABL and Quality Control (QC) Levey-Jennings and Equipment Calibration models."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class QualityControlRun(Base):
    __tablename__ = "qc_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id: Mapped[str] = mapped_column(String(36), ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    analyzer_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("analyzers.id", ondelete="SET NULL"), nullable=True)
    test_id: Mapped[str] = mapped_column(String(36), ForeignKey("tests.id", ondelete="CASCADE"), nullable=False, index=True)
    parameter_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("test_parameters.id", ondelete="SET NULL"), nullable=True)

    control_name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "Biorad Lyphochek Assayed"
    control_lot_number: Mapped[str] = mapped_column(String(100), nullable=False)
    control_level: Mapped[str] = mapped_column(String(30), nullable=False, default="NORMAL")  # NORMAL, LOW, HIGH
    
    expected_mean: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    expected_sd: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    measured_value: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    deviation_sd: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)  # (measured - mean) / sd
    
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="IN_CONTROL")  # IN_CONTROL, WARNING, OUT_OF_CONTROL
    westgard_violation: Mapped[str | None] = mapped_column(String(30), nullable=True)  # 1_2s, 1_3s, 2_2s, R_4s, 4_1s, 10_x
    
    operator_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action_taken: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    test = relationship("Test")
    operator = relationship("User", foreign_keys=[operator_id])


class EquipmentCalibration(Base):
    __tablename__ = "equipment_calibrations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id: Mapped[str] = mapped_column(String(36), ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    analyzer_id: Mapped[str] = mapped_column(String(36), ForeignKey("analyzers.id", ondelete="CASCADE"), nullable=False, index=True)

    calibration_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    next_due_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    calibrated_by: Mapped[str] = mapped_column(String(255), nullable=False)  # Service Engineer / Cert Agency
    certificate_no: Mapped[str] = mapped_column(String(100), nullable=False)
    
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="VALID")  # VALID, EXPIRED, DUE_SOON
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    certificate_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    analyzer = relationship("Analyzer")

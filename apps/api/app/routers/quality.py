"""NABL Quality Control (QC), Levey-Jennings and Equipment Calibration API router."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.quality import QualityControlRun, EquipmentCalibration
from app.models.pathology import Analyzer, Test
from app.models.core import Branch
from app.security.tenant_guard import get_tenant_context, TenantContext

router = APIRouter(prefix="/quality", tags=["quality"])


class QCRunCreate(BaseModel):
    branch_id: str | None = None
    analyzer_id: str | None = None
    test_id: str
    parameter_id: str | None = None
    control_name: str = "Bio-Rad Lyphochek Assayed"
    control_lot_number: str = "LOT-2026-B1"
    control_level: str = "NORMAL"  # NORMAL, LOW, HIGH
    expected_mean: float = Field(..., gt=0)
    expected_sd: float = Field(..., gt=0)
    measured_value: float = Field(..., gt=0)
    action_taken: str | None = None


class CalibrationCreate(BaseModel):
    branch_id: str | None = None
    analyzer_id: str
    calibration_date: datetime
    next_due_date: datetime
    calibrated_by: str = Field(..., min_length=2)
    certificate_no: str = Field(..., min_length=2)
    remarks: str | None = None


def evaluate_westgard_rules(dev_sd: float) -> tuple[str, str | None]:
    """Evaluate classic Westgard rules for a single QC run based on Z-score / deviation SD."""
    abs_sd = abs(dev_sd)
    if abs_sd <= 2.0:
        return "IN_CONTROL", None
    elif 2.0 < abs_sd <= 3.0:
        return "WARNING", "1_2s Warning (Value exceeded ±2 SD)"
    else:
        return "OUT_OF_CONTROL", "1_3s Rejection Rule Violated (Value exceeded ±3 SD)"


@router.get("/qc-runs")
def list_qc_runs(
    analyzer_id: str | None = None,
    test_id: str | None = None,
    status: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    query = db.query(QualityControlRun).filter(QualityControlRun.tenant_id == tenant_ctx.tenant_id)
    if analyzer_id:
        query = query.filter(QualityControlRun.analyzer_id == analyzer_id)
    if test_id:
        query = query.filter(QualityControlRun.test_id == test_id)
    if status:
        query = query.filter(QualityControlRun.status == status.upper())

    runs = query.order_by(QualityControlRun.timestamp.desc()).limit(limit).all()

    # Auto-seed mock runs if empty
    if not runs:
        b = db.query(Branch).filter(Branch.tenant_id == tenant_ctx.tenant_id).first()
        branch_id = b.id if b else "default-branch"
        t = db.query(Test).filter(Test.tenant_id == tenant_ctx.tenant_id).first()
        test_id_seed = t.id if t else str(uuid.uuid4())

        mock_values = [
            (95.4, 95.0, 2.5),
            (96.1, 95.0, 2.5),
            (94.8, 95.0, 2.5),
            (95.2, 95.0, 2.5),
            (100.2, 95.0, 2.5),  # 1_2s warning
            (95.8, 95.0, 2.5),
        ]
        for m_val, mean, sd in mock_values:
            dev = (m_val - mean) / sd
            st, viol = evaluate_westgard_rules(dev)
            qr = QualityControlRun(
                id=str(uuid.uuid4()),
                tenant_id=tenant_ctx.tenant_id,
                branch_id=branch_id,
                test_id=test_id_seed,
                control_name="Bio-Rad Lyphochek Assayed",
                control_lot_number="LOT-2026-B1",
                control_level="NORMAL",
                expected_mean=Decimal(str(mean)),
                expected_sd=Decimal(str(sd)),
                measured_value=Decimal(str(m_val)),
                deviation_sd=Decimal(str(round(dev, 2))),
                status=st,
                westgard_violation=viol,
                timestamp=datetime.utcnow(),
            )
            db.add(qr)
        db.commit()
        runs = query.order_by(QualityControlRun.timestamp.desc()).limit(limit).all()

    out = []
    for r in runs:
        out.append({
            "id": r.id,
            "test_id": r.test_id,
            "test_name": r.test.name if r.test else "Investigation",
            "control_name": r.control_name,
            "control_lot_number": r.control_lot_number,
            "control_level": r.control_level,
            "expected_mean": float(r.expected_mean),
            "expected_sd": float(r.expected_sd),
            "measured_value": float(r.measured_value),
            "deviation_sd": float(r.deviation_sd),
            "status": r.status,
            "westgard_violation": r.westgard_violation,
            "action_taken": r.action_taken,
            "timestamp": r.timestamp.isoformat(),
        })
    return out


@router.post("/qc-runs", status_code=status.HTTP_201_CREATED)
def record_qc_run(
    payload: QCRunCreate,
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    branch_id = payload.branch_id
    if not branch_id:
        b = db.query(Branch).filter(Branch.tenant_id == tenant_ctx.tenant_id).first()
        branch_id = b.id if b else "default-branch"

    dev = (payload.measured_value - payload.expected_mean) / payload.expected_sd
    qc_status, violation = evaluate_westgard_rules(dev)

    qc_run = QualityControlRun(
        id=str(uuid.uuid4()),
        tenant_id=tenant_ctx.tenant_id,
        branch_id=branch_id,
        analyzer_id=payload.analyzer_id,
        test_id=payload.test_id,
        parameter_id=payload.parameter_id,
        control_name=payload.control_name,
        control_lot_number=payload.control_lot_number,
        control_level=payload.control_level.upper(),
        expected_mean=Decimal(str(payload.expected_mean)),
        expected_sd=Decimal(str(payload.expected_sd)),
        measured_value=Decimal(str(payload.measured_value)),
        deviation_sd=Decimal(str(round(dev, 2))),
        status=qc_status,
        westgard_violation=violation,
        action_taken=payload.action_taken,
        timestamp=datetime.utcnow(),
    )
    db.add(qc_run)
    db.commit()
    db.refresh(qc_run)
    return {
        "id": qc_run.id,
        "deviation_sd": float(qc_run.deviation_sd),
        "status": qc_run.status,
        "westgard_violation": qc_run.westgard_violation,
        "message": "QC run logged successfully",
    }


@router.get("/calibrations")
def list_calibrations(
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    calibs = (
        db.query(EquipmentCalibration)
        .filter(EquipmentCalibration.tenant_id == tenant_ctx.tenant_id)
        .order_by(EquipmentCalibration.next_due_date.asc())
        .all()
    )
    out = []
    for c in calibs:
        out.append({
            "id": c.id,
            "analyzer_id": c.analyzer_id,
            "analyzer_name": c.analyzer.name if c.analyzer else "Clinical Analyzer",
            "calibration_date": c.calibration_date.strftime("%Y-%m-%d"),
            "next_due_date": c.next_due_date.strftime("%Y-%m-%d"),
            "calibrated_by": c.calibrated_by,
            "certificate_no": c.certificate_no,
            "status": c.status,
            "remarks": c.remarks,
        })
    return out


@router.post("/calibrations", status_code=status.HTTP_201_CREATED)
def record_calibration(
    payload: CalibrationCreate,
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    branch_id = payload.branch_id
    if not branch_id:
        b = db.query(Branch).filter(Branch.tenant_id == tenant_ctx.tenant_id).first()
        branch_id = b.id if b else "default-branch"

    status_val = "VALID"
    if payload.next_due_date < datetime.utcnow():
        status_val = "EXPIRED"

    cal = EquipmentCalibration(
        id=str(uuid.uuid4()),
        tenant_id=tenant_ctx.tenant_id,
        branch_id=branch_id,
        analyzer_id=payload.analyzer_id,
        calibration_date=payload.calibration_date,
        next_due_date=payload.next_due_date,
        calibrated_by=payload.calibrated_by,
        certificate_no=payload.certificate_no,
        status=status_val,
        remarks=payload.remarks,
        created_at=datetime.utcnow(),
    )
    db.add(cal)
    db.commit()
    db.refresh(cal)
    return {
        "id": cal.id,
        "certificate_no": cal.certificate_no,
        "status": cal.status,
        "message": "Equipment calibration registered successfully",
    }


"""Radiology and Imaging Investigation Workstation API router."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.radiology import RadiologyOrder, RadiologyFinding, RadiologyAttachment
from app.models.patient import Patient
from app.models.core import Branch
from app.security.tenant_guard import get_tenant_context, TenantContext

router = APIRouter(prefix="/radiology", tags=["radiology"])


class RadiologyOrderCreate(BaseModel):
    branch_id: str | None = None
    patient_id: str
    modality: str = Field(..., pattern="^(XRAY|USG|CT|MRI|ECG|ECHO)$")
    procedure_name: str = Field(..., min_length=3)
    clinical_history: str | None = None
    referring_doctor: str | None = None


class RadiologyFindingCreate(BaseModel):
    technique: str | None = None
    comparison: str | None = None
    findings: str = Field(..., min_length=5)
    impression: str = Field(..., min_length=5)
    recommendations: str | None = None
    is_final: bool = False


@router.get("/templates")
def list_radiology_templates() -> list[dict[str, Any]]:
    return [
        {
            "id": "tpl_cxr_normal",
            "modality": "XRAY",
            "name": "Chest X-Ray PA View — Normal",
            "technique": "Standard digital PA view of the chest was acquired in full inspiration.",
            "findings": (
                "Both lungs are clear with normal bronchovascular markings. No focal consolidation, pneumothorax, "
                "or pleural effusion is identified. The cardiothoracic ratio is within normal limits (<0.50). "
                "The mediastinal contours, hila, and aortic arch appear unremarkable. Both hemidiaphragms and "
                "costophrenic angles are sharp. The visualised bony thorax and soft tissue structures are intact."
            ),
            "impression": "Normal radiographic appearance of the chest. No active cardiopulmonary disease detected.",
        },
        {
            "id": "tpl_usg_abd_normal",
            "modality": "USG",
            "name": "Ultrasound Whole Abdomen — Normal",
            "technique": "Real-time high-resolution gray-scale and color Doppler sonography of the abdomen.",
            "findings": (
                "Liver: Normal in size (13.2 cm), contour, and parenchymal echogenicity. No focal lesion or intrahepatic "
                "biliary dilatation.\n"
                "Gallbladder: Well distended, lumen is anechoic with no calculus, sludge, or wall thickening.\n"
                "Pancreas & Spleen: Normal size, contour, and homogeneous echotexture.\n"
                "Kidneys: Both kidneys are normal in size, shape, and cortical thickness. Corticomedullary differentiation "
                "is preserved. No calculus, hydronephrosis, or mass lesion.\n"
                "Urinary Bladder: Normal wall thickness, smooth mucosal outline with no calculus or intravesical mass."
            ),
            "impression": "Normal ultrasonographic evaluation of the abdomen and pelvis.",
        },
        {
            "id": "tpl_ecg_normal",
            "modality": "ECG",
            "name": "12-Lead Electrocardiogram — Normal Sinus Rhythm",
            "technique": "Standard resting 12-lead electrocardiogram (25 mm/s, 10 mm/mV).",
            "findings": (
                "Heart Rate: 72 bpm. Rhythm: Normal Sinus Rhythm. PR Interval: 148 ms. QRS Duration: 84 ms. "
                "QT/QTc: 380/416 ms. P axis, QRS axis, and T axis are normal (+52°). No ST-segment elevation or "
                "depression. No pathological Q waves."
            ),
            "impression": "Normal 12-lead Electrocardiogram (ECG). Normal Sinus Rhythm.",
        },
    ]


@router.get("/orders")
def list_radiology_orders(
    modality: str | None = None,
    status: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    query = db.query(RadiologyOrder).filter(RadiologyOrder.tenant_id == tenant_ctx.tenant_id)
    if modality:
        query = query.filter(RadiologyOrder.modality == modality.upper())
    if status:
        query = query.filter(RadiologyOrder.status == status.upper())

    orders = query.order_by(RadiologyOrder.created_at.desc()).limit(limit).all()
    out = []
    for o in orders:
        pat_name = f"{o.patient.first_name} {o.patient.last_name or ''}".strip() if o.patient else "Unknown"
        out.append({
            "id": o.id,
            "accession_no": o.accession_no,
            "patient_id": o.patient_id,
            "patient_name": pat_name,
            "patient_uhid": o.patient.patient_no if o.patient else None,
            "modality": o.modality,
            "procedure_name": o.procedure_name,
            "clinical_history": o.clinical_history,
            "referring_doctor": o.referring_doctor,
            "status": o.status,
            "created_at": o.created_at.isoformat(),
            "has_findings": len(o.findings) > 0,
        })
    return out


@router.post("/orders", status_code=status.HTTP_201_CREATED)
def create_radiology_order(
    payload: RadiologyOrderCreate,
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    pat = (
        db.query(Patient)
        .filter(Patient.tenant_id == tenant_ctx.tenant_id, Patient.id == payload.patient_id)
        .first()
    )
    if not pat:
        raise HTTPException(status_code=404, detail="Patient not found")

    branch_id = payload.branch_id
    if not branch_id:
        b = db.query(Branch).filter(Branch.tenant_id == tenant_ctx.tenant_id).first()
        branch_id = b.id if b else "default-branch"

    accession_no = f"RAD{datetime.utcnow().strftime('%y%m%d')}{str(uuid.uuid4())[:4].upper()}"

    order = RadiologyOrder(
        id=str(uuid.uuid4()),
        tenant_id=tenant_ctx.tenant_id,
        branch_id=branch_id,
        patient_id=payload.patient_id,
        accession_no=accession_no,
        modality=payload.modality.upper(),
        procedure_name=payload.procedure_name,
        clinical_history=payload.clinical_history,
        referring_doctor=payload.referring_doctor,
        status="PENDING",
        created_at=datetime.utcnow(),
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return {
        "id": order.id,
        "accession_no": order.accession_no,
        "modality": order.modality,
        "procedure_name": order.procedure_name,
        "status": order.status,
        "message": "Radiology order scheduled successfully",
    }


@router.get("/orders/{order_id}")
def get_radiology_order_details(
    order_id: str,
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    order = (
        db.query(RadiologyOrder)
        .filter(RadiologyOrder.tenant_id == tenant_ctx.tenant_id, RadiologyOrder.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Radiology order not found")

    pat_name = f"{order.patient.first_name} {order.patient.last_name or ''}".strip() if order.patient else "Unknown"

    latest_finding = order.findings[-1] if order.findings else None

    return {
        "id": order.id,
        "accession_no": order.accession_no,
        "patient": {
            "id": order.patient.id,
            "name": pat_name,
            "uhid": order.patient.patient_no,
            "age": order.patient.age_years,
            "gender": order.patient.sex,
        },
        "modality": order.modality,
        "procedure_name": order.procedure_name,
        "clinical_history": order.clinical_history,
        "referring_doctor": order.referring_doctor,
        "status": order.status,
        "created_at": order.created_at.isoformat(),
        "finding": {
            "id": latest_finding.id,
            "technique": latest_finding.technique,
            "comparison": latest_finding.comparison,
            "findings": latest_finding.findings,
            "impression": latest_finding.impression,
            "recommendations": latest_finding.recommendations,
            "status": latest_finding.status,
            "finalized_at": latest_finding.finalized_at.isoformat() if latest_finding.finalized_at else None,
        } if latest_finding else None,
    }


@router.post("/orders/{order_id}/findings")
def save_radiology_findings(
    order_id: str,
    payload: RadiologyFindingCreate,
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    order = (
        db.query(RadiologyOrder)
        .filter(RadiologyOrder.tenant_id == tenant_ctx.tenant_id, RadiologyOrder.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Radiology order not found")

    now = datetime.utcnow()
    finding_status = "FINALIZED" if payload.is_final else "DRAFT"

    finding = RadiologyFinding(
        id=str(uuid.uuid4()),
        tenant_id=tenant_ctx.tenant_id,
        order_id=order.id,
        technique=payload.technique,
        comparison=payload.comparison,
        findings=payload.findings,
        impression=payload.impression,
        recommendations=payload.recommendations,
        status=finding_status,
        finalized_at=now if payload.is_final else None,
        created_at=now,
    )
    db.add(finding)

    order.status = "FINALIZED" if payload.is_final else "REPORT_DRAFTED"
    if payload.is_final:
        order.completed_at = now

    db.commit()
    db.refresh(finding)
    return {
        "finding_id": finding.id,
        "order_id": order.id,
        "status": finding.status,
        "message": "Radiology report finalized successfully" if payload.is_final else "Findings saved as draft",
    }

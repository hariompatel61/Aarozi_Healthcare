"""Structured Clinical Diagnostic Report & Delivery API router."""
from __future__ import annotations

import json
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.reporting import ReportTemplate, Report
from app.reporting.template_service import (
    create_report_template,
    get_report_template,
    list_report_templates,
)
from app.reporting.render_pipeline import generate_report_document
from app.reporting.signature_service import register_digital_signature
from app.reporting.delivery_service import deliver_report as execute_deliver_report
from app.rbac.engine import enforce_permission
from app.security.auth import get_current_user
from app.security.tenant_guard import get_tenant_context, TenantContext

router = APIRouter(prefix="/reports", tags=["reports"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class TemplateCreateRequest(BaseModel):
    name: str
    code: str
    template_type: str = "pathology"
    department_id: str | None = None
    template_schema: dict[str, Any]
    header_config_json: dict[str, Any] | None = None
    footer_config_json: dict[str, Any] | None = None
    is_active: bool = True


class RenderReportRequest(BaseModel):
    template_id: str | None = None
    output_format: str = "html"  # html or pdf


class DigitalSignRegisterRequest(BaseModel):
    user_id: str
    name: str
    qualifications: str | None = None
    designation: str | None = None
    registration_no: str | None = None
    signature_image_data: str | None = None
    stamp_text: str | None = None


class DeliverReportRequest(BaseModel):
    channel: str = "email"  # print, download, email, sms, whatsapp
    recipient: str
    metadata: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Report Listing & Delivery Endpoints
# ---------------------------------------------------------------------------

@router.get("")
def list_reports(
    status: str | None = None,
    search: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_tenant_context),
    current_user: Any = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """List diagnostic reports released or approved for delivery."""
    from app.models.patient import Patient
    if current_user is not None:
        enforce_permission(db, current_user, "report.view" if "report.view" in getattr(current_user, "permissions", ["report.view"]) else "order.view")

    tenant_id = tenant_context.tenant_id if tenant_context else "AAROZI_HQ"
    query = (
        db.query(Report, Patient)
        .join(Patient, Report.patient_id == Patient.id)
        .filter(Report.tenant_id == tenant_id)
    )
    if status and status.lower() != "all":
        query = query.filter(Report.status == status.lower())
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            (Report.report_no.ilike(term))
            | (Patient.patient_no.ilike(term))
            | (Patient.first_name.ilike(term))
            | (Patient.last_name.ilike(term))
            | (Patient.mobile_normalized.ilike(term))
        )
    reports = query.order_by(Report.created_at.desc()).offset(offset).limit(limit).all()
    return [
        {
            "id": r.id,
            "report_no": r.report_no,
            "patient_uhid": p.patient_no,
            "patient_name": f"{p.first_name} {p.last_name or ''}".strip(),
            "mobile": p.mobile_normalized or "N/A",
            "investigations": r.notes or "Diagnostic Panel",
            "released_at": r.released_at.strftime("%d %b %Y, %I:%M %p") if r.released_at else "Pending Release",
            "signed_by": "Authorized Pathologist",
            "delivery_status": "Released" if r.released_at else "Pending Dispatch",
            "status": r.status,
            "qr_token": r.qr_token,
        }
        for r, p in reports
    ]


# ---------------------------------------------------------------------------
# Template Endpoints
# ---------------------------------------------------------------------------

@router.get("/templates")
def get_templates(
    template_type: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_tenant_context),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    """List diagnostic report layout templates."""
    enforce_permission(db, current_user, "report.template.manage")

    templates, total = list_report_templates(
        db,
        tenant_context=tenant_context,
        category=template_type,
        limit=limit,
        offset=offset,
    )
    return {
        "total": total,
        "items": [
            {
                "id": t.id,
                "name": t.name,
                "code": t.code,
                "category": t.category,
                "version": t.version,
                "status": t.status,
            }
            for t in templates
        ],
    }


@router.get("/templates/{template_id}")
def get_template(
    template_id: str,
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_tenant_context),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    """Retrieve full schema of a report template for the visual designer."""
    enforce_permission(db, current_user, "report.template.manage")

    try:
        t = get_report_template(db, tenant_context=tenant_context, template_id=template_id)
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))

    return {
        "id": t.id,
        "name": t.name,
        "code": t.code,
        "category": t.category,
        "schema_json": t.schema_json,
        "version": t.version,
        "status": t.status,
    }


@router.post("/templates/create", status_code=status.HTTP_201_CREATED)
def save_template(
    payload: TemplateCreateRequest,
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_tenant_context),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    """Create and validate a new structured report template schema."""
    enforce_permission(db, current_user, "report.template.manage")

    try:
        t = create_report_template(
            db,
            tenant_context=tenant_context,
            name=payload.name,
            code=payload.code,
            category=payload.template_type,
            schema_dict=payload.template_schema,
            is_global=False,
            status="active" if payload.is_active else "inactive",
            actor_user_id=getattr(current_user, "id", None),
        )
        db.commit()
        db.refresh(t)
    except Exception as err:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    return {"id": t.id, "name": t.name, "code": t.code, "version": t.version}


# ---------------------------------------------------------------------------
# Report Generation & Document Rendering Endpoints
# ---------------------------------------------------------------------------

@router.post("/render/{result_id}")
def generate_result_report(
    result_id: str,
    payload: RenderReportRequest,
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_tenant_context),
    current_user: Any = Depends(get_current_user),
) -> Response:
    """Compile result data and render clinical report (HTML or binary PDF)."""
    enforce_permission(db, current_user, "report.release")

    try:
        doc = generate_report_document(
            db,
            tenant_context=tenant_context,
            result_id=result_id,
            template_id=payload.template_id,
            output_format=payload.output_format,
        )
        db.commit()
    except Exception as err:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    if payload.output_format == "pdf":
        return Response(content=doc["payload"], media_type="application/pdf")
    else:
        return Response(content=doc["payload"], media_type="text/html")


# ---------------------------------------------------------------------------
# Digital Signatures & Delivery Endpoints
# ---------------------------------------------------------------------------

@router.post("/signatures", status_code=status.HTTP_201_CREATED)
def register_clinician_signature(
    payload: DigitalSignRegisterRequest,
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_tenant_context),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    """Register or update controlled digital signature profile for a clinician/pathologist."""
    enforce_permission(db, current_user, "report.template.manage")

    try:
        sig = register_digital_signature(
            db,
            tenant_context=tenant_context,
            user_id=payload.user_id,
            name=payload.name,
            qualifications=payload.qualifications,
            designation=payload.designation,
            registration_no=payload.registration_no,
            signature_image_data=payload.signature_image_data,
            stamp_text=payload.stamp_text,
            actor_user_id=getattr(current_user, "id", None),
        )
        db.commit()
        db.refresh(sig)
    except Exception as err:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    return {"id": sig.id, "user_id": sig.user_id, "name": sig.name, "is_default": sig.is_default}


@router.post("/{report_id}/deliver")
def dispatch_report(
    report_id: str,
    payload: DeliverReportRequest,
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_tenant_context),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    """Dispatch report via specified delivery channel (email, SMS, WhatsApp, download, print)."""
    enforce_permission(db, current_user, "report.deliver")

    try:
        delivery = execute_deliver_report(
            db,
            tenant_context=tenant_context,
            report_id=report_id,
            channel=payload.channel,
            recipient=payload.recipient,
            metadata=payload.metadata,
            actor_user_id=getattr(current_user, "id", None),
        )
        db.commit()
        db.refresh(delivery)
    except Exception as err:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    meta = {}
    if delivery.metadata_json:
        try:
            meta = json.loads(delivery.metadata_json)
        except Exception:
            pass

    return {
        "id": delivery.id,
        "report_id": delivery.report_id,
        "channel": delivery.channel,
        "status": delivery.status,
        "error_message": delivery.error_message,
        "whatsapp_url": meta.get("whatsapp_web_url"),
        "formatted_message": meta.get("formatted_message"),
    }

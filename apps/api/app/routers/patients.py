"""Patient API router for registration, search, duplicates detection and merge."""
from __future__ import annotations

from datetime import date
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.core import Tenant
from app.models.pathology import Order
from app.models.patient import Patient
from app.models.billing import Invoice, ReferralPartner
from app.patient.duplicates import (
    detect_duplicates,
    execute_patient_merge,
)
from app.patient.search import search_patients
from app.patient.service import register_patient, PatientRegistrationError
from app.rbac.engine import enforce_permission
from app.security.auth import get_current_user
from app.security.tenant_guard import get_tenant_context, TenantContext

router = APIRouter(prefix="/patients", tags=["patients"])


class PatientIdentifierInput(BaseModel):
    type: str
    value: str
    is_primary: bool = False


class PatientRegisterRequest(BaseModel):
    first_name: str
    last_name: str | None = None
    sex: str
    date_of_birth: date | None = None
    age_years: int | None = None
    mobile: str | None = None
    mobile_normalized: str | None = None
    email: str | None = None
    blood_group: str | None = None
    address_json: dict[str, Any] | None = None
    identifiers: list[PatientIdentifierInput] | None = None
    client_pc_id: str | None = None


class PatientResponse(BaseModel):
    id: str
    patient_no: str
    first_name: str
    last_name: str | None = None
    sex: str
    date_of_birth: date | None = None
    age_years: int | None = None
    mobile: str | None = None
    mobile_normalized: str | None = None
    city: str | None = None
    address: str | None = None
    email: str | None = None
    blood_group: str | None = None
    status: str
    tests: str | None = None
    order_status: str | None = None
    time: str | None = None
    amount: float | None = None
    invoice_id: str | None = None
    invoice_no: str | None = None
    referral_doctor: str | None = None
    referral_partner_id: str | None = None
    created_at: str | None = None

    model_config = ConfigDict(from_attributes=True)


class DuplicateCheckRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    mobile: str | None = None
    identifier_type: str | None = None
    identifier_value: str | None = None
    date_of_birth: date | None = None
    threshold: float = Field(0.6, ge=0.0, le=1.0)
    limit: int = Field(10, ge=1, le=50)
    exclude_patient_id: str | None = None


class DuplicateMatchResponse(BaseModel):
    patient_id: str
    patient_no: str
    first_name: str
    last_name: str | None = None
    mobile: str | None = None
    date_of_birth: date | None = None
    match_score: float
    reasons: list[str]


class PatientMergeRequest(BaseModel):
    source_patient_id: str
    target_patient_id: str
    reason: str


class PatientMergeResponse(BaseModel):
    audit_id: str
    source_patient_id: str
    target_patient_id: str
    reason: str
    created_at: str
    merge_details: dict[str, Any]


@router.post("/register", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def create_patient(
    payload: PatientRegisterRequest,
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_tenant_context),
    current_user: Any = Depends(get_current_user),
) -> PatientResponse:
    """Register a new patient with multi-tenant isolation and auditable sequence."""
    enforce_permission(db, current_user, "patient.register")

    identifiers_dict = None
    if payload.identifiers:
        identifiers_dict = [ident.model_dump() for ident in payload.identifiers]

    phone_val = payload.mobile or payload.mobile_normalized

    try:
        patient = register_patient(
            db,
            tenant_context=tenant_context,
            first_name=payload.first_name,
            last_name=payload.last_name,
            sex=payload.sex,
            date_of_birth=payload.date_of_birth,
            age_years=payload.age_years,
            mobile=phone_val,
            email=payload.email,
            blood_group=payload.blood_group,
            address_json=payload.address_json,
            identifiers=identifiers_dict,
            client_pc_id=payload.client_pc_id,
        )
        db.commit()
        db.refresh(patient)
    except PatientRegistrationError as err:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    addr_data = patient.address_json or {} if isinstance(patient.address_json, dict) else {}

    return PatientResponse(
        id=patient.id,
        patient_no=patient.patient_no,
        first_name=patient.first_name,
        last_name=patient.last_name,
        sex=patient.sex,
        date_of_birth=patient.date_of_birth,
        age_years=patient.age_years,
        mobile=patient.mobile_normalized,
        mobile_normalized=patient.mobile_normalized,
        city=addr_data.get("city"),
        address=addr_data.get("address"),
        email=patient.email,
        blood_group=patient.blood_group,
        status=patient.status,
        created_at=patient.created_at.isoformat() if patient.created_at else None,
    )


@router.get("", response_model=list[PatientResponse])
def list_or_search_patients(
    query: str | None = Query(None, description="Search by name, UHID, mobile or barcode"),
    search: str | None = Query(None, description="Search query alias"),
    referral_partner_id: str | None = Query(None, description="Filter by referral partner ID"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_tenant_context),
    current_user: Any = Depends(get_current_user),
) -> list[PatientResponse]:
    """Search or list patients for the current tenant with live order and billing relations."""
    if current_user is not None:
        enforce_permission(db, current_user, "patient.view")

    tenant_id = tenant_context.tenant_id if tenant_context else "AAROZI_HQ"
    t_obj = db.query(Tenant).filter((Tenant.id == tenant_id) | (Tenant.code == tenant_id)).first()
    if t_obj:
        tenant_id = t_obj.id

    raw_q = query if query is not None else search
    q_str = raw_q.strip() if isinstance(raw_q, str) and raw_q.strip() else None
    ref_partner_str = referral_partner_id.strip() if isinstance(referral_partner_id, str) else None
    lim = limit if isinstance(limit, int) else 50
    off = offset if isinstance(offset, int) else 0

    if q_str:
        patients = search_patients(db, tenant_context, q_str, limit=lim, offset=off)
    elif ref_partner_str:
        order_patient_ids = [row[0] for row in db.query(Order.patient_id).filter(Order.tenant_id == tenant_id, Order.referral_partner_id == ref_partner_str).distinct().all()]
        inv_patient_ids = [row[0] for row in db.query(Invoice.patient_id).filter(Invoice.tenant_id == tenant_id, Invoice.referral_partner_id == ref_partner_str).distinct().all()]
        all_patient_ids = list(set([pid for pid in (order_patient_ids + inv_patient_ids) if pid]))
        patients = (
            db.query(Patient)
            .filter(Patient.tenant_id == tenant_id, Patient.id.in_(all_patient_ids))
            .order_by(Patient.created_at.desc())
            .offset(off)
            .limit(lim)
            .all()
        )
    else:
        patients = (
            db.query(Patient)
            .filter(Patient.tenant_id == tenant_id)
            .order_by(Patient.created_at.desc())
            .offset(off)
            .limit(lim)
            .all()
        )

    out = []
    for p in patients:
        ord_obj = db.query(Order).filter(Order.patient_id == p.id).order_by(Order.ordered_at.desc()).first()
        inv_obj = db.query(Invoice).filter(Invoice.patient_id == p.id).order_by(Invoice.created_at.desc()).first()

        test_names = "Diagnostic Panel"
        ord_status = p.status.capitalize()
        ord_time = p.created_at.strftime("%I:%M %p") if p.created_at else "-"
        if ord_obj:
            t_names = [itm.test.short_name or itm.test.name for itm in ord_obj.items if itm.test]
            if t_names:
                test_names = ", ".join(t_names)
            ord_status = ord_obj.status.capitalize()
            if ord_obj.ordered_at:
                ord_time = ord_obj.ordered_at.strftime("%I:%M %p")
        elif inv_obj and inv_obj.items:
            test_names = ", ".join([itm.description for itm in inv_obj.items])

        amount = 0.0
        invoice_id = None
        invoice_no = None
        ref_partner_id = None
        ref_doctor = "Direct Walk-in"

        if inv_obj:
            amount = float(getattr(inv_obj, "grand_total", getattr(inv_obj, "total_amount", 0.0)) or 0.0)
            invoice_id = inv_obj.id
            invoice_no = inv_obj.invoice_no
            ref_partner_id = inv_obj.referral_partner_id

        if not ref_partner_id and ord_obj:
            ref_partner_id = ord_obj.referral_partner_id

        if ref_partner_id:
            partner = db.query(ReferralPartner).filter(ReferralPartner.id == ref_partner_id).first()
            if partner:
                ref_doctor = partner.name

        addr_dict = p.address_json or {} if isinstance(p.address_json, dict) else {}
        city_val = addr_dict.get("city")
        address_val = addr_dict.get("address")

        out.append(PatientResponse(
            id=p.id,
            patient_no=p.patient_no,
            first_name=p.first_name,
            last_name=p.last_name,
            sex=p.sex,
            date_of_birth=p.date_of_birth,
            age_years=p.age_years,
            mobile=p.mobile_normalized,
            mobile_normalized=p.mobile_normalized,
            city=city_val,
            address=address_val,
            email=p.email,
            blood_group=p.blood_group,
            status=ord_status,
            tests=test_names,
            order_status=ord_status,
            time=ord_time,
            amount=amount,
            invoice_id=invoice_id,
            invoice_no=invoice_no,
            referral_doctor=ref_doctor,
            referral_partner_id=ref_partner_id,
            created_at=p.created_at.isoformat() if p.created_at else None,
        ))

    return out


@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_tenant_context),
    current_user: Any = Depends(get_current_user),
) -> PatientResponse:
    """Retrieve patient details by ID or UHID/patient_no with relational data."""
    enforce_permission(db, current_user, "patient.view")

    patient = (
        db.query(Patient)
        .filter(
            Patient.tenant_id == tenant_context.tenant_id,
            (Patient.id == patient_id) | (Patient.patient_no == patient_id),
        )
        .first()
    )
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Patient '{patient_id}' not found")

    ord_obj = db.query(Order).filter(Order.patient_id == patient.id).order_by(Order.ordered_at.desc()).first()
    inv_obj = db.query(Invoice).filter(Invoice.patient_id == patient.id).order_by(Invoice.created_at.desc()).first()

    test_names = "Diagnostic Panel"
    ord_status = patient.status.capitalize()
    ord_time = patient.created_at.strftime("%I:%M %p") if patient.created_at else "-"
    if ord_obj:
        t_names = [itm.test.short_name or itm.test.name for itm in ord_obj.items if itm.test]
        if t_names:
            test_names = ", ".join(t_names)
        ord_status = ord_obj.status.capitalize()
        if ord_obj.ordered_at:
            ord_time = ord_obj.ordered_at.strftime("%I:%M %p")
    elif inv_obj and inv_obj.items:
        test_names = ", ".join([itm.description for itm in inv_obj.items])

    amount = 0.0
    invoice_id = None
    invoice_no = None
    ref_partner_id = None
    ref_doctor = "Direct Walk-in"

    if inv_obj:
        amount = float(getattr(inv_obj, "grand_total", getattr(inv_obj, "total_amount", 0.0)) or 0.0)
        invoice_id = inv_obj.id
        invoice_no = inv_obj.invoice_no
        ref_partner_id = inv_obj.referral_partner_id

    if not ref_partner_id and ord_obj:
        ref_partner_id = ord_obj.referral_partner_id

    if ref_partner_id:
        partner = db.query(ReferralPartner).filter(ReferralPartner.id == ref_partner_id).first()
        if partner:
            ref_doctor = partner.name

    return PatientResponse(
        id=patient.id,
        patient_no=patient.patient_no,
        first_name=patient.first_name,
        last_name=patient.last_name,
        sex=patient.sex,
        date_of_birth=patient.date_of_birth,
        age_years=patient.age_years,
        mobile_normalized=patient.mobile_normalized,
        email=patient.email,
        blood_group=patient.blood_group,
        status=ord_status,
        tests=test_names,
        order_status=ord_status,
        time=ord_time,
        amount=amount,
        invoice_id=invoice_id,
        invoice_no=invoice_no,
        referral_doctor=ref_doctor,
        referral_partner_id=ref_partner_id,
        created_at=patient.created_at.isoformat() if patient.created_at else None,
    )


@router.post("/duplicates/check", response_model=list[DuplicateMatchResponse])
def check_patient_duplicates(
    payload: DuplicateCheckRequest,
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_tenant_context),
    current_user: Any = Depends(get_current_user),
) -> list[DuplicateMatchResponse]:
    """Check potential duplicates before registration or during workflow."""
    enforce_permission(db, current_user, "patient.view")

    matches = detect_duplicates(
        db,
        tenant_context=tenant_context,
        first_name=payload.first_name,
        last_name=payload.last_name,
        mobile=payload.mobile,
        identifier_type=payload.identifier_type,
        identifier_value=payload.identifier_value,
        date_of_birth=payload.date_of_birth,
        threshold=payload.threshold,
        limit=payload.limit,
        exclude_patient_id=payload.exclude_patient_id,
    )

    return [
        DuplicateMatchResponse(
            patient_id=m.patient.id,
            patient_no=m.patient.patient_no,
            first_name=m.patient.first_name,
            last_name=m.patient.last_name,
            mobile=m.patient.mobile_normalized,
            date_of_birth=m.patient.date_of_birth,
            match_score=m.match_score,
            reasons=m.reasons,
        )
        for m in matches
    ]


@router.post("/merge", response_model=PatientMergeResponse, status_code=status.HTTP_200_OK)
def merge_patients(
    payload: PatientMergeRequest,
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_tenant_context),
    current_user: Any = Depends(get_current_user),
) -> PatientMergeResponse:
    """Execute a controlled patient merge with authorization and durable audit."""
    enforce_permission(db, current_user, "patient.merge")

    merge_audit = execute_patient_merge(
        db,
        tenant_context=tenant_context,
        source_patient_id=payload.source_patient_id,
        target_patient_id=payload.target_patient_id,
        reason=payload.reason,
        actor_user_id=getattr(current_user, "id", None),
    )
    db.commit()

    return PatientMergeResponse(
        audit_id=merge_audit.id,
        source_patient_id=merge_audit.source_patient_id,
        target_patient_id=merge_audit.target_patient_id,
        reason=merge_audit.reason,
        created_at=merge_audit.created_at.isoformat() if merge_audit.created_at else "",
        merge_details=merge_audit.merge_details_json,
    )

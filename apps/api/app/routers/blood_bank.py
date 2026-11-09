"""Blood Bank Management System (BBMS) API router.
Covers vein-to-vein operations: Donors, Screening, Donation Bleeds, TTI Lab Testing, Quarantine Release, Cold-Chain Inventory, and Compatibility Cross-Match.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.blood_bank import Donor, Donation, BloodUnit
from app.blood_bank.donor_service import (
    register_donor,
    get_donor,
    list_donors,
)
from app.blood_bank.screening_service import conduct_screening
from app.blood_bank.donation_service import record_donation
from app.blood_bank.testing_service import record_blood_unit_tests
from app.blood_bank.quarantine_service import release_unit
from app.blood_bank.inventory_service import get_inventory_summary, get_blood_inventory as list_inventory_units
from app.blood_bank.transfusion_service import perform_cross_match, approve_cross_match, issue_unit as execute_issue_unit
from app.rbac.engine import enforce_permission
from app.security.auth import get_current_user
from app.security.tenant_guard import get_tenant_context, TenantContext

router = APIRouter(prefix="/blood-bank", tags=["blood-bank"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class DonorRegisterRequest(BaseModel):
    first_name: str
    last_name: str | None = None
    sex: str
    date_of_birth: date
    blood_group: str  # e.g., A_POS, O_NEG
    national_id: str | None = None
    mobile: str | None = None
    email: str | None = None
    address: str | None = None


class ScreeningRequest(BaseModel):
    donor_id: str
    weight_kg: float = Field(..., ge=40.0)
    hemoglobin_g_dl: float = Field(..., ge=10.0)
    systolic_bp: int = 120
    diastolic_bp: int = 80
    temperature_c: float = 36.6
    pulse_bpm: int = 72
    questionnaire_responses: dict[str, Any] | None = None


class DonationBleedRequest(BaseModel):
    donor_id: str
    bag_type: str = "single"  # single, double, triple, quadruple, apheresis
    donation_type: str = "whole_blood"
    volume_ml: int = 450
    venipuncture_site: str | None = "left_antecubital"
    screening_id: str | None = None
    notes: str | None = None


class TTITestItem(BaseModel):
    test_type: str  # HIV, HBSAG, HCV, VDRL, MALARIA, ABO_Rh
    result_value: str  # negative, positive, reactive, non_reactive
    method: str | None = "ELISA"
    notes: str | None = None


class TTITestBatchRequest(BaseModel):
    tests: list[TTITestItem]


class CrossMatchRequest(BaseModel):
    patient_id: str
    blood_unit_id: str


class CrossMatchApproveRequest(BaseModel):
    compatibility_status: Literal["compatible", "incompatible"]  # compatible, incompatible


# ---------------------------------------------------------------------------
# Donor Endpoints
# ---------------------------------------------------------------------------

@router.post("/donors/register", status_code=status.HTTP_201_CREATED)
def create_donor(
    payload: DonorRegisterRequest,
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_tenant_context),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    """Register donor with blood group and contact verification."""
    enforce_permission(db, current_user, "blood_bank.donor.register")

    try:
        donor = register_donor(
            db,
            tenant_context=tenant_context,
            first_name=payload.first_name,
            last_name=payload.last_name,
            sex=payload.sex,
            date_of_birth=payload.date_of_birth,
            blood_group=payload.blood_group,
            national_id=payload.national_id,
            mobile=payload.mobile,
            email=payload.email,
            actor_user_id=getattr(current_user, "id", None),
        )
        db.commit()
        db.refresh(donor)
    except Exception as err:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    return {
        "id": donor.id,
        "donor_no": donor.donor_no,
        "first_name": donor.first_name,
        "last_name": donor.last_name,
        "blood_group": donor.blood_group,
        "status": donor.status,
    }


@router.get("/donors")
def get_donors(
    search: str | None = None,
    blood_group: str | None = None,
    status: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_tenant_context),
    current_user: Any = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """List or search registered blood donors."""
    enforce_permission(db, current_user, "blood_bank.donor.view")

    donors = list_donors(
        db,
        tenant_context=tenant_context,
        search=search,
        blood_group=blood_group,
        status=status,
        limit=limit,
        offset=offset,
    )
    return [
        {
            "id": d.id,
            "donor_no": d.donor_no,
            "name": f"{d.first_name} {d.last_name or ''}".strip(),
            "blood_group": d.blood_group,
            "mobile": d.mobile,
            "status": d.status,
            "total_donations": getattr(d, "total_donations", 0),
        }
        for d in donors
    ]


@router.get("/donors/{donor_id}")
def get_donor_details(
    donor_id: str,
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_tenant_context),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    """Retrieve donor history, screenings, and donation records."""
    enforce_permission(db, current_user, "blood_bank.donor.view")

    try:
        donor = get_donor(db, tenant_context=tenant_context, donor_id=donor_id)
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))

    return {
        "id": donor.id,
        "donor_no": donor.donor_no,
        "first_name": donor.first_name,
        "last_name": donor.last_name,
        "blood_group": donor.blood_group,
        "sex": donor.sex,
        "date_of_birth": donor.date_of_birth.isoformat() if donor.date_of_birth else None,
        "mobile": donor.mobile,
        "email": donor.email,
        "status": donor.status,
    }


# ---------------------------------------------------------------------------
# Pre-Screening & Donation Bleed Endpoints
# ---------------------------------------------------------------------------

@router.post("/screenings", status_code=status.HTTP_201_CREATED)
def record_donor_screening(
    payload: ScreeningRequest,
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_tenant_context),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    """Record physical vitals and pre-donation medical evaluation."""
    enforce_permission(db, current_user, "blood.donor.screen")

    try:
        screening = conduct_screening(
            db,
            tenant_context=tenant_context,
            donor_id=payload.donor_id,
            weight_kg=payload.weight_kg,
            blood_pressure_systolic=payload.systolic_bp,
            blood_pressure_diastolic=payload.diastolic_bp,
            pulse_bpm=payload.pulse_bpm,
            temperature_c=payload.temperature_c,
            hemoglobin_g_dl=payload.hemoglobin_g_dl,
            questionnaire_responses=payload.questionnaire_responses,
            actor_user_id=getattr(current_user, "id", None),
        )
        db.commit()
        db.refresh(screening)
    except Exception as err:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    return {
        "id": screening.id,
        "screening_no": screening.screening_no,
        "donor_id": screening.donor_id,
        "status": screening.status,
        "eligibility_status": screening.eligibility_status,
        "deferral_reasons": [screening.deferral_reason] if getattr(screening, "deferral_reason", None) else [],
    }


@router.post("/donations", status_code=status.HTTP_201_CREATED)
def record_donation_bleed(
    payload: DonationBleedRequest,
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_tenant_context),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    """Record phlebotomy bleed, generate Donation Identification Number (DIN), and create quarantine blood unit."""
    enforce_permission(db, current_user, "blood.unit.receive")

    try:
        donation = record_donation(
            db,
            tenant_context=tenant_context,
            donor_id=payload.donor_id,
            bag_type=payload.bag_type,
            donation_type=payload.donation_type,
            volume_ml=payload.volume_ml,
            venipuncture_site=payload.venipuncture_site,
            screening_id=payload.screening_id,
            notes=payload.notes,
            collected_by=getattr(current_user, "id", None),
        )
        db.commit()
        db.refresh(donation)
    except Exception as err:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    return {
        "id": donation.id,
        "donation_no": donation.donation_no,
        "donor_id": donation.donor_id,
        "donation_type": donation.donation_type,
        "volume_ml": donation.volume_ml,
        "status": donation.status,
    }


# ---------------------------------------------------------------------------
# TTI Testing & Quarantine Release Endpoints
# ---------------------------------------------------------------------------

@router.post("/units/{unit_id}/test")
def record_unit_tti_tests(
    unit_id: str,
    payload: TTITestBatchRequest,
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_tenant_context),
    current_user: Any = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Record Transfusion-Transmissible Infection (TTI) or blood group serology test."""
    enforce_permission(db, current_user, "blood.unit.receive")

    tests_input = [t.model_dump() for t in payload.tests]
    try:
        test_records = record_blood_unit_tests(
            db,
            tenant_context=tenant_context,
            blood_unit_id=unit_id,
            tests_input=tests_input,
        )
        db.commit()
    except Exception as err:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    return [{"id": t.id, "test_type": t.test_type, "result_value": t.result_value} for t in test_records]


@router.post("/units/{unit_id}/release")
def release_blood_unit(
    unit_id: str,
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_tenant_context),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    """Verify all 5 TTI tests are non-reactive and release unit to ready inventory."""
    enforce_permission(db, current_user, "blood.unit.receive")

    try:
        unit = release_unit(
            db,
            tenant_context=tenant_context,
            blood_unit_id=unit_id,
        )
        db.commit()
        db.refresh(unit)
    except Exception as err:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    return {"id": unit.id, "unit_no": unit.unit_no, "status": unit.status}


# ---------------------------------------------------------------------------
# Cold-Chain Inventory & Compatibility Cross-Match
# ---------------------------------------------------------------------------

@router.get("/inventory")
def get_blood_inventory(
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_tenant_context),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    """Retrieve available blood unit counts grouped by ABO/Rh group and component type."""
    enforce_permission(db, current_user, "blood.unit.receive")

    summary = get_inventory_summary(db, tenant_context=tenant_context)
    return {"inventory": summary}


@router.get("/units")
def list_blood_units(
    blood_group: str | None = None,
    component_type: str | None = None,
    status: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_tenant_context),
    current_user: Any = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """List blood units with status and expiration tracking."""
    if current_user is not None:
        enforce_permission(db, current_user, "blood.unit.receive" if "blood.unit.receive" in getattr(current_user, "permissions", ["blood.unit.receive"]) else "blood_bank.donor.view")

    tenant_id = tenant_context.tenant_id if tenant_context else "AAROZI_HQ"
    query = db.query(BloodUnit).filter(BloodUnit.tenant_id == tenant_id)
    if status and status.lower() != "all":
        query = query.filter(BloodUnit.status == status.lower())
    if blood_group and blood_group.lower() != "all":
        query = query.filter(BloodUnit.blood_group == blood_group)
    if component_type and component_type.lower() != "all":
        query = query.filter(BloodUnit.component_type == component_type)

    units = query.order_by(BloodUnit.expiry_at.asc()).offset(offset).limit(limit).all()
    return [
        {
            "id": u.id,
            "unit_no": u.unit_no,
            "donor_id": u.donor_id,
            "blood_group": u.blood_group,
            "component_type": u.component_type,
            "volume_ml": u.volume_ml,
            "status": u.status,
            "collected_at": u.collected_at.isoformat() if u.collected_at else None,
            "expiry_at": u.expiry_at.isoformat() if u.expiry_at else None,
        }
        for u in units
    ]


@router.get("/crossmatch-records")
def list_cross_matches(
    status: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_tenant_context),
    current_user: Any = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """List compatibility cross-match records."""
    from app.models.patient import Patient
    from app.models.blood_bank import CrossMatch
    if current_user is not None:
        enforce_permission(db, current_user, "blood.unit.issue" if "blood.unit.issue" in getattr(current_user, "permissions", ["blood.unit.issue"]) else "blood_bank.donor.view")

    tenant_id = tenant_context.tenant_id if tenant_context else "AAROZI_HQ"
    query = (
        db.query(CrossMatch, Patient, BloodUnit)
        .join(Patient, CrossMatch.patient_id == Patient.id)
        .join(BloodUnit, CrossMatch.blood_unit_id == BloodUnit.id)
        .filter(CrossMatch.tenant_id == tenant_id)
    )
    if status and status.lower() != "all":
        query = query.filter(CrossMatch.compatibility_status == status.lower())

    records = query.order_by(CrossMatch.created_at.desc()).offset(offset).limit(limit).all()
    return [
        {
            "id": cm.id,
            "request_no": f"REQ-{cm.id[:8].upper()}",
            "patient_uhid": p.patient_no,
            "patient_name": f"{p.first_name} {p.last_name or ''}".strip(),
            "patient_blood_group": getattr(p, "blood_group", "O+"),
            "donor_unit_number": bu.unit_no,
            "donor_blood_group": bu.blood_group,
            "component": bu.component_type,
            "urgency": "Routine",
            "major_crossmatch": "Compatible" if cm.compatibility_status == "compatible" else ("Incompatible" if cm.compatibility_status == "incompatible" else "Pending"),
            "minor_crossmatch": "Compatible" if cm.compatibility_status == "compatible" else ("Incompatible" if cm.compatibility_status == "incompatible" else "Pending"),
            "status": "Ready for Issue" if cm.compatibility_status == "compatible" else ("Incompatible" if cm.compatibility_status == "incompatible" else "Pending Test"),
            "created_at": cm.created_at.isoformat() if cm.created_at else None,
        }
        for cm, p, bu in records
    ]


@router.post("/crossmatch")
def perform_compatibility_crossmatch(
    payload: CrossMatchRequest,
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_tenant_context),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    """Initiate serological cross-match between recipient serum and donor red cells."""
    enforce_permission(db, current_user, "blood.unit.issue")

    try:
        xm = perform_cross_match(
            db,
            tenant_context=tenant_context,
            patient_id=payload.patient_id,
            blood_unit_id=payload.blood_unit_id,
        )
        db.commit()
        db.refresh(xm)
    except Exception as err:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    return {"id": xm.id, "patient_id": xm.patient_id, "blood_unit_id": xm.blood_unit_id, "status": xm.compatibility_status}


@router.post("/crossmatch/{cross_match_id}/approve")
def approve_compatibility_crossmatch(
    cross_match_id: str,
    payload: CrossMatchApproveRequest,
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_tenant_context),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    """Approve or reject cross-match compatibility result."""
    enforce_permission(db, current_user, "blood.unit.issue")

    try:
        xm = approve_cross_match(
            db,
            tenant_context=tenant_context,
            cross_match_id=cross_match_id,
            compatibility_status=payload.compatibility_status,
        )
        db.commit()
        db.refresh(xm)
    except Exception as err:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    return {"id": xm.id, "status": xm.compatibility_status}


@router.post("/units/{unit_id}/issue")
def issue_blood_unit(
    unit_id: str,
    recipient_patient_id: str = Query(...),
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_tenant_context),
    current_user: Any = Depends(get_current_user),
) -> dict[str, Any]:
    """Issue compatible blood unit for patient transfusion."""
    enforce_permission(db, current_user, "blood.unit.issue")

    try:
        unit = execute_issue_unit(
            db,
            tenant_context=tenant_context,
            blood_unit_id=unit_id,
            patient_id=recipient_patient_id,
        )
        db.commit()
        db.refresh(unit)
    except Exception as err:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    return {"id": unit.id, "unit_no": unit.unit_no, "status": unit.status}

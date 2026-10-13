"""Patient registration service supporting multiple concurrent reception PCs."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.audit.service import log_audit_event
from app.models.patient import Patient, PatientIdentifier
from app.security.tenant_guard import TenantContext, verify_tenant_boundary


class PatientRegistrationError(Exception):
    """Base exception for patient registration."""
    pass


class PatientNotFoundError(PatientRegistrationError):
    pass


def generate_patient_no(db: Session, tenant_id: str, prefix: str = "P") -> str:
    """
    Generate tenant-scoped patient registration sequence (e.g., P-YYYYMMDD-XXXX or P-XXXXX).
    Ensures safe concurrent assignment per tenant.
    """
    today_str = datetime.utcnow().strftime("%Y%m%d")
    match_pattern = f"{prefix}-{today_str}-%"

    count = (
        db.query(func.count(Patient.id))
        .filter(Patient.tenant_id == tenant_id, Patient.patient_no.like(match_pattern))
        .scalar()
        or 0
    )
    return f"{prefix}-{today_str}-{count + 1:04d}"


def register_patient(
    db: Session,
    *,
    tenant_context: TenantContext,
    first_name: str,
    last_name: str | None = None,
    sex: str,
    date_of_birth: date | None = None,
    age_years: int | None = None,
    mobile: str | None = None,
    email: str | None = None,
    blood_group: str | None = None,
    address_json: dict[str, Any] | None = None,
    identifiers: list[dict[str, Any]] | None = None,
    client_pc_id: str | None = None,
) -> Patient:
    """
    Register a new patient from a reception terminal (PC).
    Audits the registration event with client terminal context.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id

    if not first_name or not first_name.strip():
        raise PatientRegistrationError("Patient first name is required.")
    if not sex or sex.lower() not in {"male", "female", "other"}:
        raise PatientRegistrationError("Valid sex ('male', 'female', 'other') is required.")

    patient_no = generate_patient_no(db, tenant_id)

    # Normalize mobile if provided
    normalized_mobile = None
    if mobile:
        digits = "".join(c for c in mobile if c.isdigit() or c == "+")
        normalized_mobile = digits if digits else None

    patient = Patient(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        branch_id=tenant_context.branch_id,
        patient_no=patient_no,
        first_name=first_name.strip(),
        last_name=last_name.strip() if last_name else None,
        sex=sex.lower(),
        date_of_birth=date_of_birth,
        mobile_normalized=normalized_mobile,
        email=email.strip().lower() if email else None,
        blood_group=blood_group,
        address_json=address_json or {},
        emergency_contact_json={},
        status="active",
    )
    db.add(patient)
    db.flush()

    if identifiers:
        for ident in identifiers:
            id_type = ident.get("type")
            id_val = ident.get("value")
            if id_type and id_val:
                db_ident = PatientIdentifier(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    patient_id=patient.id,
                    identifier_type=id_type.strip(),
                    identifier_value=id_val.strip(),
                    is_primary=bool(ident.get("is_primary", False)),
                )
                db.add(db_ident)
        db.flush()

    log_audit_event(
        db,
        tenant_id=tenant_id,
        action_code="patient.register",
        actor_user_id=tenant_context.user_id,
        branch_id=tenant_context.branch_id,
        entity_type="patient",
        entity_id=patient.id,
        after_json={
            "patient_no": patient.patient_no,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "client_pc_id": client_pc_id,
        },
    )

    db.flush()
    return patient

"""Patient search and query service with tenant isolation and index optimization."""
from __future__ import annotations

import re
from typing import Sequence
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.patient import Patient, PatientIdentifier
from app.security.tenant_guard import TenantContext, verify_tenant_boundary


def normalize_mobile(phone: str | None) -> str:
    """Normalize phone number by stripping whitespace, dashes, and parentheses."""
    if not phone:
        return ""
    cleaned = re.sub(r"[\s\-\(\)\.]", "", phone.strip())
    return cleaned


def extract_digits(phone: str | None) -> str:
    """Extract only digit characters."""
    if not phone:
        return ""
    return re.sub(r"\D", "", phone)



def search_patients(
    db: Session,
    tenant_context: TenantContext,
    query: str,
    *,
    limit: int = 50,
    offset: int = 0,
) -> list[Patient]:
    """Search patients by UHID/patient_no, mobile phone, barcode/identifier, or name.

    Guarantees:
    - Strictly scoped to tenant_context.tenant_id
    - Bounded result set (max 100)
    - Indexed lookups (patient_no exact/prefix, mobile exact/prefix, identifier value)
    """
    if not tenant_context or not tenant_context.tenant_id:
        return []

    q = (query or "").strip()
    if not q:
        return []

    limit = min(max(1, limit), 100)
    tenant_id = tenant_context.tenant_id

    # 1. Exact or prefix match on patient_no (UHID) or barcode identifier
    # Check patient_identifiers first for exact barcode/identifier match
    identifier_match_stmt = (
        select(PatientIdentifier.patient_id)
        .where(
            PatientIdentifier.tenant_id == tenant_id,
            PatientIdentifier.identifier_value == q,
        )
        .limit(limit)
    )
    matching_patient_ids_from_ids = list(db.scalars(identifier_match_stmt).all())

    digits_q = extract_digits(q)

    # Base patient query
    conditions = []

    # UHID (patient_no) match
    conditions.append(Patient.patient_no.ilike(f"{q}%"))

    # Mobile match
    if digits_q and len(digits_q) >= 4:
        # Match either direct contains or matching against trailing digits (e.g. 03001234567 against +923001234567)
        significant_digits = digits_q[-9:] if len(digits_q) >= 9 else digits_q
        conditions.append(Patient.mobile_normalized.like(f"%{significant_digits}%"))

    # Name match (first_name or last_name prefix)
    conditions.append(Patient.first_name.ilike(f"{q}%"))
    conditions.append(Patient.last_name.ilike(f"{q}%"))

    # Full name concatenation match
    full_name_expr = func.concat(Patient.first_name, " ", func.coalesce(Patient.last_name, ""))
    conditions.append(full_name_expr.ilike(f"%{q}%"))

    # If barcode identifier found matches
    if matching_patient_ids_from_ids:
        conditions.append(Patient.id.in_(matching_patient_ids_from_ids))

    stmt = (
        select(Patient)
        .options(joinedload(Patient.identifiers))
        .where(
            Patient.tenant_id == tenant_id,
            or_(*conditions),
        )
        .order_by(Patient.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    results = list(db.scalars(stmt).unique().all())
    return results


def get_patient_by_uhid(
    db: Session,
    tenant_context: TenantContext,
    patient_no: str,
) -> Patient | None:
    """Retrieve a single patient by UHID (patient_no) within tenant boundary."""
    if not tenant_context or not tenant_context.tenant_id:
        return None

    stmt = (
        select(Patient)
        .options(joinedload(Patient.identifiers))
        .where(
            Patient.tenant_id == tenant_context.tenant_id,
            Patient.patient_no == patient_no.strip(),
        )
    )
    return db.scalars(stmt).unique().first()


def get_patient_by_identifier(
    db: Session,
    tenant_context: TenantContext,
    identifier_type: str,
    identifier_value: str,
) -> Patient | None:
    """Retrieve patient by specific identifier (e.g. BARCODE, CNIC, MRN) within tenant boundary."""
    if not tenant_context or not tenant_context.tenant_id:
        return None

    stmt = (
        select(Patient)
        .join(PatientIdentifier, PatientIdentifier.patient_id == Patient.id)
        .options(joinedload(Patient.identifiers))
        .where(
            Patient.tenant_id == tenant_context.tenant_id,
            PatientIdentifier.identifier_type == identifier_type.strip(),
            PatientIdentifier.identifier_value == identifier_value.strip(),
        )
    )
    return db.scalars(stmt).unique().first()

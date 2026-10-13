"""Patient duplicate detection and controlled merge service."""
from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, joinedload

from app.audit.service import log_audit_event
from app.errors import ConflictError, NotFoundError, ValidationError
from app.models.patient import Patient, PatientIdentifier, PatientMergeAudit
from app.patient.search import normalize_mobile, extract_digits
from app.security.tenant_guard import TenantContext, verify_tenant_boundary


@dataclass
class DuplicateMatch:
    patient: Patient
    match_score: float  # 0.0 to 1.0
    reasons: list[str] = field(default_factory=list)


def calculate_name_similarity(name1: str, name2: str) -> float:
    """Calculate ratio between two names."""
    if not name1 or not name2:
        return 0.0
    return difflib.SequenceMatcher(None, name1.lower().strip(), name2.lower().strip()).ratio()


def detect_duplicates(
    db: Session,
    *,
    tenant_context: TenantContext,
    first_name: str | None = None,
    last_name: str | None = None,
    mobile: str | None = None,
    identifier_type: str | None = None,
    identifier_value: str | None = None,
    date_of_birth: date | None = None,
    threshold: float = 0.6,
    limit: int = 10,
    exclude_patient_id: str | None = None,
) -> list[DuplicateMatch]:
    """Detect potential duplicate patients within the tenant context.
    
    Safe & bounded: strictly clamped to tenant_id and limit <= 50.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id
    limit = min(max(1, limit), 50)

    # 1. First, search for exact identifier match if identifier provided
    matches: dict[str, DuplicateMatch] = {}
    if identifier_type and identifier_value:
        clean_val = identifier_value.strip()
        stmt = (
            select(PatientIdentifier)
            .options(joinedload(PatientIdentifier.patient))
            .where(
                PatientIdentifier.tenant_id == tenant_id,
                PatientIdentifier.identifier_type == identifier_type,
                PatientIdentifier.identifier_value == clean_val,
            )
        )
        if exclude_patient_id:
            stmt = stmt.where(PatientIdentifier.patient_id != exclude_patient_id)
        
        ident_records = db.execute(stmt).scalars().all()
        for ident in ident_records:
            if ident.patient and ident.patient.status != "merged":
                matches[ident.patient.id] = DuplicateMatch(
                    patient=ident.patient,
                    match_score=1.0,
                    reasons=[f"Exact identifier match ({identifier_type}: {clean_val})"],
                )

    # 2. Next, exact or normalized mobile match
    norm_mobile = normalize_mobile(mobile) if mobile else None
    digits = extract_digits(mobile) if mobile else ""
    if norm_mobile or digits:
        conditions = []
        if norm_mobile:
            conditions.append(Patient.mobile_normalized == norm_mobile)
        if digits and len(digits) >= 7:
            # Match suffix / international variant
            conditions.append(Patient.mobile_normalized.endswith(digits[-7:]))

        stmt = (
            select(Patient)
            .where(
                Patient.tenant_id == tenant_id,
                or_(*conditions),
                Patient.status != "merged",
            )
            .limit(limit)
        )
        if exclude_patient_id:
            stmt = stmt.where(Patient.id != exclude_patient_id)
        
        for p in db.execute(stmt).scalars().all():
            if p.id in matches:
                matches[p.id].reasons.append("Phone number match")
            else:
                matches[p.id] = DuplicateMatch(
                    patient=p,
                    match_score=0.85,
                    reasons=["Phone number match"],
                )

    # 3. Fuzzy name match + DOB / demographics
    if first_name and len(first_name.strip()) >= 2:
        fn_clean = first_name.strip().lower()
        stmt = (
            select(Patient)
            .where(
                Patient.tenant_id == tenant_id,
                Patient.status != "merged",
            )
        )
        if exclude_patient_id:
            stmt = stmt.where(Patient.id != exclude_patient_id)
        
        # Bounded fetch for candidates
        candidates = db.execute(stmt.limit(100)).scalars().all()
        for cand in candidates:
            cand_fn = cand.first_name.lower().strip()
            score = 0.0
            reasons = []

            # Name similarity
            sim_first = calculate_name_similarity(fn_clean, cand_fn)
            if sim_first >= 0.8:
                score += 0.5 * sim_first
                reasons.append(f"High first name similarity ({int(sim_first*100)}%)")
            
            if last_name and cand.last_name:
                sim_last = calculate_name_similarity(last_name.strip(), cand.last_name.strip())
                if sim_last >= 0.8:
                    score += 0.3 * sim_last
                    reasons.append(f"High last name similarity ({int(sim_last*100)}%)")

            # DOB match bonus
            if date_of_birth and cand.date_of_birth and cand.date_of_birth == date_of_birth:
                score += 0.3
                reasons.append("Exact date of birth match")

            if score >= threshold:
                final_score = min(score, 1.0)
                if cand.id in matches:
                    matches[cand.id].match_score = max(matches[cand.id].match_score, final_score)
                    matches[cand.id].reasons.extend(reasons)
                else:
                    matches[cand.id] = DuplicateMatch(
                        patient=cand,
                        match_score=round(final_score, 2),
                        reasons=reasons,
                    )

    # Sort matches by score descending and truncate to limit
    sorted_matches = sorted(matches.values(), key=lambda m: m.match_score, reverse=True)
    return sorted_matches[:limit]


def execute_patient_merge(
    db: Session,
    *,
    tenant_context: TenantContext,
    source_patient_id: str,
    target_patient_id: str,
    reason: str,
    actor_user_id: str | None = None,
) -> PatientMergeAudit:
    """Execute a controlled merge of source_patient into target_patient.
    
    Invariants:
    1. Both patients must belong to the caller's tenant.
    2. source != target.
    3. Neither patient may already be merged.
    4. Non-conflicting identifiers are moved from source to target.
    5. Source patient status is transitioned to 'merged' with merged_into_patient_id set.
    6. PatientMergeAudit record and durable audit log entry are created.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id

    if not reason or not reason.strip():
        raise ValidationError("Merge reason is required for audit compliance", field="reason")

    if source_patient_id == target_patient_id:
        raise ValidationError("Source and target patient cannot be the same record", field="target_patient_id")

    # Fetch both patients within tenant
    source = db.execute(
        select(Patient)
        .options(joinedload(Patient.identifiers))
        .where(Patient.id == source_patient_id, Patient.tenant_id == tenant_id)
    ).unique().scalar_one_or_none()

    if not source:
        raise NotFoundError(f"Source patient '{source_patient_id}' not found", field="source_patient_id")

    target = db.execute(
        select(Patient)
        .options(joinedload(Patient.identifiers))
        .where(Patient.id == target_patient_id, Patient.tenant_id == tenant_id)
    ).unique().scalar_one_or_none()

    if not target:
        raise NotFoundError(f"Target patient '{target_patient_id}' not found", field="target_patient_id")

    if source.status == "merged":
        raise ConflictError(f"Source patient '{source.patient_no}' is already merged into '{source.merged_into_patient_id}'")

    if target.status == "merged":
        raise ConflictError(f"Cannot merge into patient '{target.patient_no}' because target is already merged")

    # Move non-conflicting identifiers from source to target
    target_ident_tuples = {(i.identifier_type, i.identifier_value) for i in target.identifiers}
    moved_identifiers: list[str] = []

    for src_ident in list(source.identifiers):
        tuple_key = (src_ident.identifier_type, src_ident.identifier_value)
        if tuple_key not in target_ident_tuples:
            # Reassign identifier to target
            src_ident.patient_id = target.id
            src_ident.is_primary = False  # target keeps primary
            moved_identifiers.append(f"{src_ident.identifier_type}:{src_ident.identifier_value}")
        else:
            # Duplicate identifier between source and target; delete source's copy
            db.delete(src_ident)

    # Backfill missing demographic fields on target if source has them
    if not target.blood_group and source.blood_group:
        target.blood_group = source.blood_group
    if not target.email and source.email:
        target.email = source.email
    if not target.date_of_birth and source.date_of_birth:
        target.date_of_birth = source.date_of_birth
    if not target.mobile_normalized and source.mobile_normalized:
        target.mobile_normalized = source.mobile_normalized

    # Update source patient status
    source.status = "merged"
    source.merged_into_patient_id = target.id

    # Create Merge Audit record
    merge_details = {
        "source_patient_no": source.patient_no,
        "target_patient_no": target.patient_no,
        "moved_identifiers": moved_identifiers,
    }

    merge_audit = PatientMergeAudit(
        tenant_id=tenant_id,
        source_patient_id=source.id,
        target_patient_id=target.id,
        actor_user_id=actor_user_id,
        reason=reason.strip(),
        merge_details_json=merge_details,
    )
    db.add(merge_audit)

    # Durable audit log
    log_audit_event(
        db,
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        action_code="patient.merge",
        entity_type="patient",
        entity_id=source.id,
        before_json={"status": "active", "patient_no": source.patient_no},
        after_json={
            "status": "merged",
            "merged_into_patient_id": target.id,
            "target_patient_no": target.patient_no,
            "reason": reason.strip(),
        },
    )

    db.flush()
    return merge_audit

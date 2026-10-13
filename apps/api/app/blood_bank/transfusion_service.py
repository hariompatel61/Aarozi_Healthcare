"""Blood Bank Reservations, Cross-Match, Issue/Return & Adverse Events Service (P07-08 to P07-11)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.errors import NotFoundError, ValidationError, ForbiddenError, ConflictError
from app.models.blood_bank import BloodUnit, CrossMatch, AdverseEvent
from app.models.identity import Permission, RolePermission, UserRole
from app.security.tenant_guard import TenantContext
from app.blood_bank.unit_service import log_blood_movement


def _check_transfusion_permission(
    db: Session,
    *,
    tenant_context: TenantContext,
    permission_code: str = "blood.unit.issue",
) -> None:
    if tenant_context.is_superuser:
        return

    effective_user_id = tenant_context.user_id
    if not effective_user_id:
        raise ForbiddenError("Authenticated actor required for transfusion operations")

    has_perm = (
        db.query(RolePermission)
        .join(UserRole, UserRole.role_id == RolePermission.role_id)
        .join(Permission, Permission.id == RolePermission.permission_id)
        .filter(
            UserRole.user_id == effective_user_id,
            Permission.code.in_([permission_code, "blood.unit.receive", "blood.unit.issue"]),
            RolePermission.allow.is_(True),
        )
        .first()
    )
    if not has_perm:
        raise ForbiddenError(f"User lacks required permission '{permission_code}'")


def reserve_unit(
    db: Session,
    *,
    tenant_context: TenantContext,
    blood_unit_id: str,
    patient_id: str,
) -> BloodUnit:
    _check_transfusion_permission(db, tenant_context=tenant_context)
    unit = db.query(BloodUnit).filter(BloodUnit.id == blood_unit_id, BloodUnit.tenant_id == tenant_context.tenant_id).first()
    if not unit:
        raise NotFoundError("Blood unit not found")
    if unit.status != "released":
        raise ConflictError(f"Cannot reserve blood unit in status '{unit.status}'")
    old_status = unit.status
    unit.status = "reserved"
    log_blood_movement(
        db, tenant_context=tenant_context, blood_unit_id=unit.id,
        movement_type="reserve", from_status=old_status, to_status="reserved",
        patient_id=patient_id, reason="Reserved for patient order"
    )
    db.commit()
    db.refresh(unit)
    return unit

def perform_cross_match(
    db: Session,
    *,
    tenant_context: TenantContext,
    patient_id: str,
    blood_unit_id: str,
) -> CrossMatch:
    _check_transfusion_permission(db, tenant_context=tenant_context)
    unit = db.query(BloodUnit).filter(BloodUnit.id == blood_unit_id, BloodUnit.tenant_id == tenant_context.tenant_id).first()
    if not unit:
        raise NotFoundError("Blood unit not found")
    cm = CrossMatch(
        tenant_id=tenant_context.tenant_id,
        patient_id=patient_id,
        blood_unit_id=blood_unit_id,
        compatibility_status="pending",
        performed_by=tenant_context.user_id,
        performed_at=datetime.now(timezone.utc),
    )
    db.add(cm)
    db.commit()
    db.refresh(cm)
    return cm


def approve_cross_match(
    db: Session,
    *,
    tenant_context: TenantContext,
    cross_match_id: str,
    compatibility_status: str = "compatible",
) -> CrossMatch:
    _check_transfusion_permission(db, tenant_context=tenant_context)
    cm = db.query(CrossMatch).filter(CrossMatch.id == cross_match_id, CrossMatch.tenant_id == tenant_context.tenant_id).first()
    if not cm:
        raise NotFoundError("Cross-match record not found")
    cm.compatibility_status = compatibility_status
    cm.approved_by = tenant_context.user_id
    cm.approved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(cm)
    return cm


def issue_unit(
    db: Session,
    *,
    tenant_context: TenantContext,
    blood_unit_id: str,
    patient_id: str,
) -> BloodUnit:
    _check_transfusion_permission(db, tenant_context=tenant_context)
    unit = db.query(BloodUnit).filter(BloodUnit.id == blood_unit_id, BloodUnit.tenant_id == tenant_context.tenant_id).first()
    if not unit:
        raise NotFoundError("Blood unit not found")
    if unit.status not in ["released", "reserved"]:
        raise ConflictError(f"Cannot issue blood unit in status '{unit.status}'")
    old_status = unit.status
    unit.status = "issued"
    log_blood_movement(
        db, tenant_context=tenant_context, blood_unit_id=unit.id,
        movement_type="issue", from_status=old_status, to_status="issued",
        patient_id=patient_id, reason="Issued to patient/ward"
    )
    db.commit()
    db.refresh(unit)
    return unit


def return_unit(
    db: Session,
    *,
    tenant_context: TenantContext,
    blood_unit_id: str,
    reason: str,
) -> BloodUnit:
    _check_transfusion_permission(db, tenant_context=tenant_context)
    if not reason:
        raise ValidationError("Reason is required to return an issued blood unit")
    unit = db.query(BloodUnit).filter(BloodUnit.id == blood_unit_id, BloodUnit.tenant_id == tenant_context.tenant_id).first()
    if not unit:
        raise NotFoundError("Blood unit not found")
    if unit.status != "issued":
        raise ConflictError("Can only return issued blood units")
    old_status = unit.status
    unit.status = "released"
    log_blood_movement(
        db, tenant_context=tenant_context, blood_unit_id=unit.id,
        movement_type="return", from_status=old_status, to_status="released",
        reason=reason
    )
    db.commit()
    db.refresh(unit)
    return unit


def record_adverse_event(
    db: Session,
    *,
    tenant_context: TenantContext,
    blood_unit_id: str,
    patient_id: str,
    reaction_type: str,
    severity: str = "moderate",
    symptoms: str | None = None,
    action_taken: str | None = None,
) -> AdverseEvent:
    _check_transfusion_permission(db, tenant_context=tenant_context)
    ae = AdverseEvent(
        tenant_id=tenant_context.tenant_id,
        blood_unit_id=blood_unit_id,
        patient_id=patient_id,
        reaction_type=reaction_type,
        severity=severity,
        symptoms=symptoms,
        action_taken=action_taken,
        reported_by=tenant_context.user_id,
        reported_at=datetime.now(timezone.utc),
    )
    db.add(ae)
    db.commit()
    db.refresh(ae)
    return ae


"""Blood Bank Quarantine, Release, Discard & Expiry Service (P07-06)."""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.errors import NotFoundError, ValidationError, ForbiddenError, ConflictError
from app.models.blood_bank import BloodUnit
from app.models.identity import Permission, RolePermission, UserRole
from app.security.tenant_guard import TenantContext
from app.blood_bank.testing_service import check_unit_testing_clearance
from app.blood_bank.unit_service import log_blood_movement


def _check_quarantine_permission(
    db: Session,
    *,
    tenant_context: TenantContext,
    permission_code: str = "blood.unit.receive",
) -> None:
    if tenant_context.is_superuser:
        return

    effective_user_id = tenant_context.user_id
    if not effective_user_id:
        raise ForbiddenError("Authenticated actor required for blood quarantine/release operations")

    has_perm = (
        db.query(RolePermission)
        .join(UserRole, UserRole.role_id == RolePermission.role_id)
        .join(Permission, Permission.id == RolePermission.permission_id)
        .filter(
            UserRole.user_id == effective_user_id,
            Permission.code.in_([permission_code, "blood.unit.receive", "blood.unit.verify", "blood.unit.issue"]),
            RolePermission.allow.is_(True),
        )
        .first()
    )
    if not has_perm:
        raise ForbiddenError(f"User lacks required permission '{permission_code}'")


def quarantine_unit(
    db: Session,
    *,
    tenant_context: TenantContext,
    blood_unit_id: str,
    reason: str,
) -> BloodUnit:
    _check_quarantine_permission(db, tenant_context=tenant_context)
    if not reason:
        raise ValidationError("Reason is required to quarantine a blood unit")

    unit = (
        db.query(BloodUnit)
        .filter(
            BloodUnit.id == blood_unit_id,
            BloodUnit.tenant_id == tenant_context.tenant_id,
        )
        .first()
    )
    if not unit:
        raise NotFoundError("Blood unit not found")

    if unit.status in ["issued", "discarded", "expired"]:
        raise ConflictError(f"Cannot quarantine blood unit in status '{unit.status}'")

    old_status = unit.status
    unit.status = "quarantined"

    log_blood_movement(
        db,
        tenant_context=tenant_context,
        blood_unit_id=unit.id,
        movement_type="quarantine",
        from_status=old_status,
        to_status="quarantined",
        reason=reason,
    )
    db.commit()
    db.refresh(unit)
    return unit


def release_unit(
    db: Session,
    *,
    tenant_context: TenantContext,
    blood_unit_id: str,
) -> BloodUnit:
    _check_quarantine_permission(db, tenant_context=tenant_context)

    unit = (
        db.query(BloodUnit)
        .filter(
            BloodUnit.id == blood_unit_id,
            BloodUnit.tenant_id == tenant_context.tenant_id,
        )
        .first()
    )
    if not unit:
        raise NotFoundError("Blood unit not found")

    if unit.status not in ["testing", "quarantined", "collected"]:
        raise ConflictError(f"Cannot release blood unit from status '{unit.status}'")

    clearance = check_unit_testing_clearance(db, tenant_context=tenant_context, blood_unit_id=unit.id)
    if not clearance["cleared"]:
        raise ConflictError(f"Cannot release blood unit: TTI testing not cleared (missing: {clearance['missing']}, pending: {clearance['pending']}, reactive: {clearance['reactive']})")

    old_status = unit.status
    unit.status = "released"

    log_blood_movement(
        db,
        tenant_context=tenant_context,
        blood_unit_id=unit.id,
        movement_type="release",
        from_status=old_status,
        to_status="released",
        reason="TTI testing passed and quality verified",
    )
    db.commit()
    db.refresh(unit)
    return unit


def discard_unit(
    db: Session,
    *,
    tenant_context: TenantContext,
    blood_unit_id: str,
    reason: str,
) -> BloodUnit:
    _check_quarantine_permission(db, tenant_context=tenant_context)
    if not reason:
        raise ValidationError("Reason is required to discard a blood unit")

    unit = (
        db.query(BloodUnit)
        .filter(
            BloodUnit.id == blood_unit_id,
            BloodUnit.tenant_id == tenant_context.tenant_id,
        )
        .first()
    )
    if not unit:
        raise NotFoundError("Blood unit not found")

    if unit.status in ["issued", "discarded", "expired"]:
        raise ConflictError(f"Cannot discard blood unit in status '{unit.status}'")

    old_status = unit.status
    unit.status = "discarded"

    log_blood_movement(
        db,
        tenant_context=tenant_context,
        blood_unit_id=unit.id,
        movement_type="discard",
        from_status=old_status,
        to_status="discarded",
        reason=reason,
    )
    db.commit()
    db.refresh(unit)
    return unit

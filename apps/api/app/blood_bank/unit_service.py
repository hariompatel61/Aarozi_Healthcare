"""Blood Bank Unit Identity, Barcode & Traceability Service (P07-04)."""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.errors import NotFoundError, ValidationError, ForbiddenError
from app.models.blood_bank import BloodUnit, BloodMovement, Donation, Donor
from app.models.identity import Permission, RolePermission, UserRole
from app.security.tenant_guard import TenantContext


def _check_unit_permission(
    db: Session,
    *,
    tenant_context: TenantContext,
    permission_code: str = "blood.unit.receive",
    actor_user_id: str | None = None,
) -> None:
    if tenant_context.is_superuser:
        return

    effective_user_id = actor_user_id or tenant_context.user_id
    if not effective_user_id:
        raise ForbiddenError("Authenticated actor required for blood unit operations")

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


def get_blood_unit_by_barcode(
    db: Session,
    *,
    tenant_context: TenantContext,
    unit_no: str,
) -> BloodUnit:
    unit = (
        db.query(BloodUnit)
        .filter(
            BloodUnit.tenant_id == tenant_context.tenant_id,
            BloodUnit.unit_no == unit_no,
        )
        .first()
    )
    if not unit:
        raise NotFoundError(f"Blood unit with barcode/number '{unit_no}' not found")
    return unit


def log_blood_movement(
    db: Session,
    *,
    tenant_context: TenantContext,
    blood_unit_id: str,
    movement_type: str,
    from_status: str | None,
    to_status: str,
    patient_id: str | None = None,
    reason: str | None = None,
    actor_user_id: str | None = None,
) -> BloodMovement:
    movement = BloodMovement(
        tenant_id=tenant_context.tenant_id,
        blood_unit_id=blood_unit_id,
        movement_type=movement_type,
        from_status=from_status,
        to_status=to_status,
        patient_id=patient_id,
        reason=reason,
        actor_user_id=actor_user_id or tenant_context.user_id,
    )
    db.add(movement)
    db.flush()
    return movement


def update_unit_status(
    db: Session,
    *,
    tenant_context: TenantContext,
    blood_unit_id: str,
    new_status: str,
    movement_type: str = "status_change",
    reason: str | None = None,
    patient_id: str | None = None,
) -> BloodUnit:
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

    old_status = unit.status
    if old_status == new_status:
        return unit

    unit.status = new_status
    log_blood_movement(
        db,
        tenant_context=tenant_context,
        blood_unit_id=unit.id,
        movement_type=movement_type,
        from_status=old_status,
        to_status=new_status,
        patient_id=patient_id,
        reason=reason,
    )
    db.commit()
    db.refresh(unit)
    return unit


def get_unit_traceability(
    db: Session,
    *,
    tenant_context: TenantContext,
    blood_unit_id: str,
) -> dict[str, Any]:
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

    donation = db.query(Donation).filter(Donation.id == unit.donation_id).first()
    donor = db.query(Donor).filter(Donor.id == donation.donor_id).first() if donation else None

    movements = (
        db.query(BloodMovement)
        .filter(BloodMovement.blood_unit_id == unit.id)
        .order_by(BloodMovement.created_at.asc())
        .all()
    )

    return {
        "unit": unit,
        "donation": donation,
        "donor": donor,
        "movements": movements,
    }


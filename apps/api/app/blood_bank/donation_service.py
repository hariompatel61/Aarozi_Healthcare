"""Blood Bank Donation and Component Generation Service.

Handles phlebotomy/donation lifecycle, adverse event handling, donor history synchronization,
and blood component fractionation (Whole Blood, PRBC, FFP, Platelets, Cryoprecipitate).
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.audit.service import log_audit_event
from app.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.blood_bank import BloodUnit, Donation, Donor, DonorScreening
from app.models.identity import Permission, RolePermission, UserRole
from app.security.tenant_guard import TenantContext


COMPONENT_SPECIFICATIONS: dict[str, dict[str, Any]] = {
    "whole_blood": {
        "suffix": "WB",
        "shelf_life_days": 35,
        "default_volume_ml": 450,
        "storage_location": "Blood Bank Refrigerator 2-6°C",
    },
    "packed_red_cells": {
        "suffix": "PRBC",
        "shelf_life_days": 42,
        "default_volume_ml": 250,
        "storage_location": "Blood Bank Refrigerator 2-6°C",
    },
    "fresh_frozen_plasma": {
        "suffix": "FFP",
        "shelf_life_days": 365,
        "default_volume_ml": 200,
        "storage_location": "Deep Freezer -30°C",
    },
    "platelet_concentrate": {
        "suffix": "PC",
        "shelf_life_days": 5,
        "default_volume_ml": 60,
        "storage_location": "Platelet Agitator 20-24°C",
    },
    "cryoprecipitate": {
        "suffix": "CRYO",
        "shelf_life_days": 365,
        "default_volume_ml": 20,
        "storage_location": "Deep Freezer -30°C",
    },
    "single_donor_platelet": {
        "suffix": "SDP",
        "shelf_life_days": 5,
        "default_volume_ml": 250,
        "storage_location": "Platelet Agitator 20-24°C",
    },
}

BAG_TYPE_COMPONENTS: dict[str, list[str]] = {
    "single": ["whole_blood"],
    "double": ["packed_red_cells", "fresh_frozen_plasma"],
    "triple": ["packed_red_cells", "fresh_frozen_plasma", "platelet_concentrate"],
    "quadruple": [
        "packed_red_cells",
        "fresh_frozen_plasma",
        "platelet_concentrate",
        "cryoprecipitate",
    ],
    "apheresis": ["single_donor_platelet"],
}

WHOLE_BLOOD_MIN_INTERVAL_DAYS = 56


def _check_donation_permission(
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
        raise ForbiddenError("Authenticated actor required for blood bank donation operations")

    has_perm = (
        db.query(RolePermission)
        .join(UserRole, UserRole.role_id == RolePermission.role_id)
        .join(Permission, Permission.id == RolePermission.permission_id)
        .filter(
            UserRole.user_id == effective_user_id,
            Permission.code.in_([permission_code, "blood.donor.screen"]),
            RolePermission.allow.is_(True),
        )
        .first()
    )
    if not has_perm:
        raise ForbiddenError(f"User lacks required permission '{permission_code}'")


def _generate_donation_no(db: Session, tenant_id: str, donation_date: datetime) -> str:
    date_str = donation_date.strftime("%Y%m%d")
    prefix = f"DON-{date_str}-"
    count = (
        db.query(func.count(Donation.id))
        .filter(Donation.tenant_id == tenant_id, Donation.donation_no.like(f"{prefix}%"))
        .scalar()
        or 0
    )
    return f"{prefix}{count + 1:04d}"


def calculate_component_expiry(component_type: str, donation_timestamp: datetime) -> datetime:
    spec = COMPONENT_SPECIFICATIONS.get(component_type)
    shelf_days = spec["shelf_life_days"] if spec else 35
    return donation_timestamp + timedelta(days=shelf_days)



def _create_components_for_donation(
    db: Session,
    tenant_context: TenantContext,
    donation: Donation,
) -> list[BloodUnit]:
    component_types = BAG_TYPE_COMPONENTS.get(donation.bag_type, ["whole_blood"])
    created_units: list[BloodUnit] = []

    for comp in component_types:
        spec = COMPONENT_SPECIFICATIONS.get(comp, {})
        suffix = spec.get("suffix", comp.upper()[:4])
        unit_no = f"{donation.donation_no}-{suffix}"
        expiry = calculate_component_expiry(comp, donation.donated_at)
        vol = spec.get("default_volume_ml", donation.volume_ml)
        storage = spec.get("storage_location", "Blood Bank Storage")

        unit = BloodUnit(
            tenant_id=tenant_context.tenant_id,
            donation_id=donation.id,
            unit_no=unit_no,
            component_type=comp,
            blood_group=donation.blood_group,
            volume_ml=vol,
            status="collected",
            storage_location=storage,
            expiry_at=expiry,
            collected_at=donation.donated_at,
        )
        db.add(unit)
        created_units.append(unit)

    db.flush()

    for u in created_units:
        log_audit_event(
            db,
            tenant_id=tenant_context.tenant_id,
            action_code="blood.component.generated",
            actor_user_id=donation.collected_by,
            entity_type="blood_unit",
            entity_id=u.id,
            after_json={
                "unit_no": u.unit_no,
                "donation_no": donation.donation_no,
                "component_type": u.component_type,
                "blood_group": u.blood_group,
                "expiry_at": u.expiry_at.isoformat(),
            },
        )

    return created_units



def record_donation(
    db: Session,
    *,
    tenant_context: TenantContext,
    donor_id: str,
    bag_type: str = "single",
    donation_type: str = "whole_blood",
    volume_ml: int = 450,
    venipuncture_site: str | None = "left_antecubital",
    status: str = "completed",
    screening_id: str | None = None,
    notes: str | None = None,
    collected_by: str | None = None,
    donated_at: datetime | None = None,
    auto_generate_components: bool = True,
) -> Donation:
    effective_user_id = collected_by or tenant_context.user_id
    _check_donation_permission(
        db,
        tenant_context=tenant_context,
        permission_code="blood.unit.receive",
        actor_user_id=effective_user_id,
    )

    donor = (
        db.query(Donor)
        .filter(
            Donor.id == donor_id,
            Donor.tenant_id == tenant_context.tenant_id,
        )
        .first()
    )
    if not donor:
        raise NotFoundError("Donor not found")

    if donor.status in ("deferred_permanent", "deferred_temporary"):
        raise ConflictError(
            f"Donor is currently deferred ({donor.status}) and ineligible for phlebotomy"
        )

    donation_dt = donated_at or datetime.now(timezone.utc)
    donation_date = donation_dt.date() if isinstance(donation_dt, datetime) else donation_dt

    if donation_type == "whole_blood" and donor.last_donation_date:
        last_date = (
            donor.last_donation_date.date()
            if isinstance(donor.last_donation_date, datetime)
            else donor.last_donation_date
        )
        days_since = (donation_date - last_date).days
        if days_since < WHOLE_BLOOD_MIN_INTERVAL_DAYS:
            raise ConflictError(
                f"Minimum donation interval not met: {days_since} days since last donation "
                f"(minimum {WHOLE_BLOOD_MIN_INTERVAL_DAYS} days required)"
            )

    screening: DonorScreening | None = None
    if screening_id:
        screening = (
            db.query(DonorScreening)
            .filter(
                DonorScreening.id == screening_id,
                DonorScreening.tenant_id == tenant_context.tenant_id,
                DonorScreening.donor_id == donor_id,
            )
            .first()
        )
        if not screening:
            raise NotFoundError("Screening record not found for this donor")
        if screening.status != "passed":
            raise ConflictError(
                f"Cannot collect donation from non-eligible screening status: '{screening.status}'"
            )

    if bag_type not in BAG_TYPE_COMPONENTS:
        raise ValidationError(
            f"Invalid bag_type '{bag_type}'. Supported: {', '.join(BAG_TYPE_COMPONENTS.keys())}"
        )

    if volume_ml <= 0 or volume_ml > 600:
        raise ValidationError("Volume must be a positive physiological quantity (max 600 ml)")

    donation_no = _generate_donation_no(db, tenant_context.tenant_id, donation_dt)

    donation = Donation(
        tenant_id=tenant_context.tenant_id,
        donor_id=donor_id,
        screening_id=screening_id,
        donation_no=donation_no,
        donation_type=donation_type,
        bag_type=bag_type,
        volume_ml=volume_ml,
        blood_group=donor.blood_group,
        venipuncture_site=venipuncture_site,
        status=status,
        screening_status="passed" if (screening and screening.status == "passed") else "passed",
        eligibility_status="eligible",
        notes=notes,
        collected_by=effective_user_id,
        donated_at=donation_dt,
    )
    db.add(donation)
    db.flush()

    if status == "completed":
        donor.last_donation_date = donation_dt
        donor.total_donations = (donor.total_donations or 0) + 1

    if auto_generate_components and status == "completed":
        _create_components_for_donation(db, tenant_context, donation)

    db.commit()
    db.refresh(donation)

    log_audit_event(
        db,
        tenant_id=tenant_context.tenant_id,
        action_code="blood.donation.recorded",
        actor_user_id=effective_user_id,
        entity_type="donation",
        entity_id=donation.id,
        after_json={
            "donation_no": donation.donation_no,
            "donor_id": donor_id,
            "donor_no": donor.donor_no,
            "blood_group": donor.blood_group,
            "bag_type": bag_type,
            "volume_ml": volume_ml,
            "status": status,
        },
    )

    return donation



def generate_components(
    db: Session,
    *,
    tenant_context: TenantContext,
    donation_id: str,
) -> list[BloodUnit]:
    _check_donation_permission(
        db,
        tenant_context=tenant_context,
        permission_code="blood.unit.receive",
    )

    donation = (
        db.query(Donation)
        .filter(
            Donation.id == donation_id,
            Donation.tenant_id == tenant_context.tenant_id,
        )
        .first()
    )
    if not donation:
        raise NotFoundError("Donation record not found")

    if donation.status != "completed":
        raise ConflictError(
            f"Cannot generate components from donation with status '{donation.status}'"
        )

    existing = (
        db.query(BloodUnit)
        .filter(
            BloodUnit.donation_id == donation_id,
            BloodUnit.tenant_id == tenant_context.tenant_id,
        )
        .all()
    )
    if existing:
        raise ConflictError(
            f"Components already generated for donation {donation.donation_no} ({len(existing)} units exist)"
        )

    units = _create_components_for_donation(db, tenant_context, donation)
    db.commit()
    return units


def get_donation(
    db: Session,
    *,
    tenant_context: TenantContext,
    donation_id: str,
) -> Donation:
    donation = (
        db.query(Donation)
        .filter(
            Donation.id == donation_id,
            Donation.tenant_id == tenant_context.tenant_id,
        )
        .first()
    )
    if not donation:
        raise NotFoundError("Donation not found")
    return donation


def list_donations(
    db: Session,
    *,
    tenant_context: TenantContext,
    donor_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Donation]:
    query = db.query(Donation).filter(Donation.tenant_id == tenant_context.tenant_id)
    if donor_id:
        query = query.filter(Donation.donor_id == donor_id)
    if status:
        query = query.filter(Donation.status == status)

    return query.order_by(Donation.donated_at.desc()).offset(offset).limit(limit).all()


def list_blood_units(
    db: Session,
    *,
    tenant_context: TenantContext,
    donation_id: str | None = None,
    blood_group: str | None = None,
    component_type: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[BloodUnit]:
    query = db.query(BloodUnit).filter(BloodUnit.tenant_id == tenant_context.tenant_id)
    if donation_id:
        query = query.filter(BloodUnit.donation_id == donation_id)
    if blood_group:
        query = query.filter(BloodUnit.blood_group == blood_group)
    if component_type:
        query = query.filter(BloodUnit.component_type == component_type)
    if status:
        query = query.filter(BloodUnit.status == status)

    return query.order_by(BloodUnit.created_at.desc()).offset(offset).limit(limit).all()



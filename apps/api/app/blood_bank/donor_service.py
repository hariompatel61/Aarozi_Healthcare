"""Blood Bank Donor Master Service: Donor identity, registration, eligibility check, and clinical deferrals."""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select, and_, or_, desc
from sqlalchemy.orm import Session, joinedload

from app.audit.service import log_audit_event
from app.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.blood_bank import Donor, DonorDeferral
from app.models.identity import User
from app.rbac.engine import authorize_action
from app.security.tenant_guard import TenantContext, verify_tenant_boundary


VALID_BLOOD_GROUPS = {
    "A_POS", "A_NEG", "B_POS", "B_NEG",
    "AB_POS", "AB_NEG", "O_POS", "O_NEG",
}

VALID_DONOR_STATUSES = {
    "active", "deferred_temporary", "deferred_permanent", "inactive"
}


def _check_donor_permission(
    db: Session,
    *,
    tenant_context: TenantContext,
    permission_code: str,
    actor_user_id: str | None = None,
) -> None:
    user_id = actor_user_id or tenant_context.user_id
    if not user_id:
        return
    user = db.query(User).filter(User.id == user_id, User.tenant_id == tenant_context.tenant_id).first()
    if user and not authorize_action(db, user, permission_code, branch_id=tenant_context.branch_id):
        raise ForbiddenError(f"User is not authorized for '{permission_code}'")


def generate_donor_no(db: Session, tenant_id: str, prefix: str = "DNR") -> str:
    today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    match_pattern = f"{prefix}-{today_str}-%"
    count = (
        db.query(func.count(Donor.id))
        .filter(Donor.tenant_id == tenant_id, Donor.donor_no.like(match_pattern))
        .scalar()
        or 0
    )
    return f"{prefix}-{today_str}-{count + 1:04d}"


def register_donor(
    db: Session,
    *,
    tenant_context: TenantContext,
    first_name: str,
    last_name: str | None = None,
    sex: str,
    date_of_birth: date | None = None,
    blood_group: str | None = None,
    mobile: str | None = None,
    email: str | None = None,
    national_id: str | None = None,
    abha_id: str | None = None,
    patient_id: str | None = None,
    actor_user_id: str | None = None,
) -> Donor:
    """Register voluntary/replacement blood donor with eligibility validation."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id
    effective_user_id = actor_user_id or tenant_context.user_id

    _check_donor_permission(db, tenant_context=tenant_context, permission_code="blood.donor.create", actor_user_id=effective_user_id)

    clean_first = (first_name or "").strip()
    if not clean_first:
        raise ValidationError("Donor first name is required", field="first_name")

    clean_sex = (sex or "").strip().lower()
    if clean_sex not in ("male", "female", "other"):
        raise ValidationError("Valid sex is required (male, female, other)", field="sex")

    clean_bg = None
    if blood_group:
        clean_bg = blood_group.strip().upper().replace("+", "_POS").replace("-", "_NEG")
        if clean_bg not in VALID_BLOOD_GROUPS:
            raise ValidationError(f"Invalid blood group '{blood_group}'", field="blood_group")

    # Age check (Standard blood donor age: 18 - 65)
    now_date = datetime.now(timezone.utc).date()
    if date_of_birth:
        age_years = (now_date - date_of_birth).days / 365.25
        if age_years < 18:
            raise ValidationError("Blood donor must be at least 18 years of age", field="date_of_birth")
        if age_years > 65:
            raise ValidationError("Blood donor cannot be older than 65 years of age", field="date_of_birth")

    clean_mobile = mobile.strip() if mobile else None
    clean_nat = national_id.strip() if national_id else None

    # Check existing donor duplicate
    if clean_nat:
        dup = db.query(Donor).filter(Donor.tenant_id == tenant_id, Donor.national_id == clean_nat).first()
        if dup:
            raise ConflictError(f"Donor with national_id '{clean_nat}' is already registered as {dup.donor_no}")

    donor_num = generate_donor_no(db, tenant_id)

    donor = Donor(
        tenant_id=tenant_id,
        donor_no=donor_num,
        patient_id=patient_id,
        first_name=clean_first,
        last_name=last_name.strip() if last_name else None,
        date_of_birth=date_of_birth,
        sex=clean_sex,
        blood_group=clean_bg,
        mobile=clean_mobile,
        email=email.strip() if email else None,
        national_id=clean_nat,
        abha_id=abha_id.strip() if abha_id else None,
        status="active",
        total_donations=0,
    )
    db.add(donor)
    db.flush()

    log_audit_event(
        db,
        tenant_id=tenant_id,
        action_code="blood.donor.created",
        actor_user_id=effective_user_id,
        entity_type="donor",
        entity_id=donor.id,
        after_json={
            "donor_no": donor.donor_no,
            "name": f"{donor.first_name} {donor.last_name or ''}".strip(),
            "blood_group": donor.blood_group,
            "status": donor.status,
        },
    )

    db.commit()
    db.refresh(donor)
    return donor


def defer_donor(
    db: Session,
    *,
    tenant_context: TenantContext,
    donor_id: str,
    deferral_type: str,
    reason: str,
    deferred_until: datetime | None = None,
    actor_user_id: str | None = None,
) -> DonorDeferral:
    """
    Record clinical deferral against a donor (temporary or permanent).
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id
    effective_user_id = actor_user_id or tenant_context.user_id

    _check_donor_permission(db, tenant_context=tenant_context, permission_code="blood.donor.screen", actor_user_id=effective_user_id)

    donor = db.query(Donor).filter(Donor.id == donor_id, Donor.tenant_id == tenant_id).first()
    if not donor:
        raise NotFoundError(f"Donor '{donor_id}' not found")

    clean_type = (deferral_type or "").strip().lower()
    if clean_type not in ("temporary", "permanent"):
        raise ValidationError("deferral_type must be 'temporary' or 'permanent'", field="deferral_type")

    clean_reason = (reason or "").strip()
    if not clean_reason:
        raise ValidationError("Clinical deferral reason is required", field="reason")

    now = datetime.now(timezone.utc)
    if clean_type == "temporary":
        if not deferred_until or deferred_until <= now:
            raise ValidationError("deferred_until date in the future is required for temporary deferral", field="deferred_until")

    donor.status = "deferred_permanent" if clean_type == "permanent" else "deferred_temporary"

    deferral = DonorDeferral(
        tenant_id=tenant_id,
        donor_id=donor.id,
        deferral_type=clean_type,
        reason=clean_reason,
        deferred_until=deferred_until if clean_type == "temporary" else None,
        status="active",
        deferred_by=effective_user_id,
        deferred_at=now,
    )
    db.add(deferral)
    db.flush()

    log_audit_event(
        db,
        tenant_id=tenant_id,
        action_code="blood.donor.deferred",
        actor_user_id=effective_user_id,
        entity_type="donor",
        entity_id=donor.id,
        after_json={
            "deferral_id": deferral.id,
            "deferral_type": clean_type,
            "reason": clean_reason,
            "status": donor.status,
            "deferred_until": deferred_until.isoformat() if deferred_until else None,
        },
    )

    db.commit()
    db.refresh(deferral)
    return deferral


def lift_deferral(
    db: Session,
    *,
    tenant_context: TenantContext,
    deferral_id: str,
    lift_reason: str,
    actor_user_id: str | None = None,
) -> DonorDeferral:
    """Lift active temporary deferral after clinical review."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id
    effective_user_id = actor_user_id or tenant_context.user_id

    _check_donor_permission(db, tenant_context=tenant_context, permission_code="blood.donor.screen", actor_user_id=effective_user_id)

    deferral = (
        db.query(DonorDeferral)
        .join(Donor)
        .filter(DonorDeferral.id == deferral_id, DonorDeferral.tenant_id == tenant_id)
        .first()
    )
    if not deferral:
        raise NotFoundError(f"Deferral '{deferral_id}' not found")

    if deferral.status != "active":
        raise ConflictError(f"Cannot lift deferral in status '{deferral.status}'")

    if deferral.deferral_type == "permanent":
        raise ConflictError("Permanent deferrals cannot be lifted routinely without medical director authorization")

    clean_reason = (lift_reason or "").strip()
    if not clean_reason:
        raise ValidationError("Medical justification is required to lift deferral", field="lift_reason")

    now = datetime.now(timezone.utc)
    deferral.status = "lifted"
    deferral.lift_reason = clean_reason
    deferral.lifted_by = effective_user_id
    deferral.lifted_at = now

    donor = deferral.donor
    remaining = (
        db.query(DonorDeferral)
        .filter(
            DonorDeferral.donor_id == donor.id,
            DonorDeferral.status == "active",
            DonorDeferral.id != deferral.id,
        )
        .first()
    )
    if not remaining:
        donor.status = "active"

    log_audit_event(
        db,
        tenant_id=tenant_id,
        action_code="blood.donor.deferral_lifted",
        actor_user_id=effective_user_id,
        entity_type="donor_deferral",
        entity_id=deferral.id,
        after_json={"status": "lifted", "reason": clean_reason, "donor_status": donor.status},
    )

    db.commit()
    db.refresh(deferral)
    return deferral



def _as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def check_donor_eligibility(
    db: Session,
    *,
    tenant_context: TenantContext,
    donor_id: str,
    donation_type: str = "whole_blood",
) -> dict[str, Any]:
    """
    Check donor eligibility based on status, active deferrals, and donation interval.
    Whole blood minimum interval: 56 days.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    donor = (
        db.query(Donor)
        .options(joinedload(Donor.deferrals))
        .filter(Donor.id == donor_id, Donor.tenant_id == tenant_context.tenant_id)
        .first()
    )
    if not donor:
        raise NotFoundError(f"Donor '{donor_id}' not found")

    now = datetime.now(timezone.utc)

    # 1. Check permanent deferral
    perm_def = next((d for d in donor.deferrals if d.status == "active" and d.deferral_type == "permanent"), None)
    if perm_def:
        return {
            "is_eligible": False,
            "status": "deferred_permanent",
            "reason": f"Permanently deferred: {perm_def.reason}",
            "days_until_eligible": None,
        }

    # 2. Check active temporary deferral
    active_temp = [d for d in donor.deferrals if d.status == "active" and d.deferral_type == "temporary" and d.deferred_until and _as_utc(d.deferred_until) > now]
    if active_temp:
        latest = sorted(active_temp, key=lambda d: _as_utc(d.deferred_until), reverse=True)[0]
        latest_dt = _as_utc(latest.deferred_until)
        days_left = (latest_dt - now).days + 1
        return {
            "is_eligible": False,
            "status": "deferred_temporary",
            "reason": f"Temporarily deferred: {latest.reason} (until {latest_dt.strftime('%d-%b-%Y')})",
            "days_until_eligible": max(1, days_left),
        }

    # 3. Check minimum donation interval (56 days for whole blood)
    min_interval_days = 56 if donation_type == "whole_blood" else 14
    if donor.last_donation_date:
        last_dt = _as_utc(donor.last_donation_date)
        next_allowed = last_dt + timedelta(days=min_interval_days)
        if now < next_allowed:
            days_left = (next_allowed - now).days + 1
            return {
                "is_eligible": False,
                "status": "interval_not_met",
                "reason": f"Minimum donation interval ({min_interval_days} days) not met. Next eligible on {next_allowed.strftime('%d-%b-%Y')}",
                "days_until_eligible": max(1, days_left),
            }

    return {
        "is_eligible": True,
        "status": "eligible",
        "reason": None,
        "days_until_eligible": 0,
    }



def get_donor(
    db: Session,
    *,
    tenant_context: TenantContext,
    donor_id: str,
) -> Donor:
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    donor = (
        db.query(Donor)
        .options(joinedload(Donor.deferrals))
        .filter(Donor.id == donor_id, Donor.tenant_id == tenant_context.tenant_id)
        .first()
    )
    if not donor:
        raise NotFoundError(f"Donor '{donor_id}' not found")
    return donor


def list_donors(
    db: Session,
    *,
    tenant_context: TenantContext,
    blood_group: str | None = None,
    status: str | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Donor], int]:
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    limit = min(max(1, limit), 100)
    offset = max(0, offset)

    query = db.query(Donor).filter(Donor.tenant_id == tenant_context.tenant_id)
    if blood_group:
        query = query.filter(Donor.blood_group == blood_group.strip().upper())
    if status:
        query = query.filter(Donor.status == status.strip().lower())
    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Donor.donor_no.ilike(s),
                Donor.first_name.ilike(s),
                Donor.last_name.ilike(s),
                Donor.mobile.ilike(s),
                Donor.national_id.ilike(s),
            )
        )

    total = query.count()
    items = query.order_by(desc(Donor.created_at)).offset(offset).limit(limit).all()
    return items, total


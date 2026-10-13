"""Referral Partner Master service: Doctors, Hospitals, Labs, and Collection Centres.

Provides multi-tenant master record management, rule configurations, bounded pagination,
server-side RBAC enforcement, and audit logging.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.audit.service import log_audit_event
from app.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.billing import ReferralPartner, ReferralRule
from app.models.identity import User
from app.rbac.engine import authorize_action
from app.security.tenant_guard import TenantContext, verify_tenant_boundary


VALID_PARTNER_TYPES = {
    "doctor",
    "hospital",
    "lab",
    "external_lab",
    "collection_centre",
    "collection_center",
    "corporate",
    "corporate_account",
}

CANONICAL_PARTNER_TYPES = {
    "doctor": "doctor",
    "hospital": "hospital",
    "lab": "lab",
    "external_lab": "lab",
    "collection_centre": "collection_centre",
    "collection_center": "collection_centre",
    "corporate": "corporate",
    "corporate_account": "corporate",
}

VALID_STATUSES = {"active", "inactive"}
VALID_SCOPE_TYPES = {"all", "test", "department", "package", "profile"}


class ReferralPartnerNotFoundError(NotFoundError):
    """Raised when referral partner does not exist."""
    pass


class ReferralRuleNotFoundError(NotFoundError):
    """Raised when referral rule does not exist."""
    pass


def _enforce_user_permission(
    db: Session,
    user_id: str | None,
    tenant_id: str,
    permission_code: str,
    branch_id: str | None = None,
) -> None:
    """Enforce server-side RBAC if user_id is provided."""
    if not user_id:
        return
    user = db.get(User, user_id)
    if not user or user.tenant_id != tenant_id:
        raise ForbiddenError(f"User {user_id} not found or tenant mismatch")
    if not authorize_action(db, user, permission_code, branch_id=branch_id):
        raise ForbiddenError(f"User does not have required permission: {permission_code}")



def create_referral_partner(
    db: Session,
    *,
    tenant_context: TenantContext,
    partner_type: str,
    name: str,
    phone: str | None = None,
    email: str | None = None,
    status: str = "active",
    actor_user_id: str | None = None,
) -> ReferralPartner:
    """Create a new referral partner master record."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id
    effective_user_id = actor_user_id or tenant_context.user_id

    _enforce_user_permission(
        db,
        effective_user_id,
        tenant_id,
        "referral.rule.manage",
        tenant_context.branch_id,
    )

    clean_name = (name or "").strip()
    if not clean_name:
        raise ValidationError("Referral partner name cannot be empty", field="name")

    raw_type = (partner_type or "").strip().lower()
    if raw_type not in VALID_PARTNER_TYPES:
        raise ValidationError(
            f"Invalid partner_type '{partner_type}'. Allowed types: {sorted(VALID_PARTNER_TYPES)}",
            field="partner_type",
        )
    canonical_type = CANONICAL_PARTNER_TYPES[raw_type]

    clean_status = (status or "active").strip().lower()
    if clean_status not in VALID_STATUSES:
        raise ValidationError(f"Invalid status '{status}'", field="status")

    clean_phone = phone.strip() if phone else None
    clean_email = email.strip().lower() if email else None

    existing = db.execute(
        select(ReferralPartner).where(
            ReferralPartner.tenant_id == tenant_id,
            ReferralPartner.partner_type == canonical_type,
            func.lower(ReferralPartner.name) == clean_name.lower(),
        )
    ).scalars().first()
    if existing:
        raise ConflictError(
            f"Referral partner '{clean_name}' of type '{canonical_type}' already exists"
        )

    partner = ReferralPartner(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        partner_type=canonical_type,
        name=clean_name,
        phone=clean_phone,
        email=clean_email,
        status=clean_status,
        created_at=datetime.now(timezone.utc),
    )
    db.add(partner)
    db.flush()

    log_audit_event(
        db,
        tenant_id=tenant_id,
        actor_user_id=effective_user_id,
        branch_id=tenant_context.branch_id,
        action_code="referral.partner.created",
        entity_type="referral_partner",
        entity_id=partner.id,
        after_json={
            "partner_id": partner.id,
            "partner_type": partner.partner_type,
            "name": partner.name,
            "phone": partner.phone,
            "email": partner.email,
            "status": partner.status,
        },
    )

    db.commit()
    db.refresh(partner)
    return partner


def get_referral_partner(
    db: Session,
    *,
    tenant_context: TenantContext,
    partner_id: str,
    actor_user_id: str | None = None,
) -> ReferralPartner:
    """Fetch referral partner by ID with tenant isolation and optional rules."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    effective_user_id = actor_user_id or tenant_context.user_id

    _enforce_user_permission(
        db,
        effective_user_id,
        tenant_context.tenant_id,
        "referral.view",
        tenant_context.branch_id,
    )

    partner = db.execute(
        select(ReferralPartner)
        .options(joinedload(ReferralPartner.rules))
        .where(
            ReferralPartner.tenant_id == tenant_context.tenant_id,
            ReferralPartner.id == partner_id,
        )
    ).scalars().unique().first()

    if not partner:
        raise ReferralPartnerNotFoundError(f"Referral partner '{partner_id}' not found")
    return partner



def list_referral_partners(
    db: Session,
    *,
    tenant_context: TenantContext,
    partner_type: str | None = None,
    status: str | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
    actor_user_id: str | None = None,
) -> tuple[list[ReferralPartner], int]:
    """List referral partners with tenant scoping and bounded pagination."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id
    effective_user_id = actor_user_id or tenant_context.user_id

    _enforce_user_permission(
        db,
        effective_user_id,
        tenant_id,
        "referral.view",
        tenant_context.branch_id,
    )

    clamped_limit = max(1, min(limit, 100))
    clamped_offset = max(0, offset)

    query = select(ReferralPartner).where(ReferralPartner.tenant_id == tenant_id)

    if partner_type:
        raw_type = partner_type.strip().lower()
        canonical_type = CANONICAL_PARTNER_TYPES.get(raw_type, raw_type)
        query = query.where(ReferralPartner.partner_type == canonical_type)

    if status:
        query = query.where(ReferralPartner.status == status.strip().lower())

    if search:
        search_filter = f"%{search.strip().lower()}%"
        query = query.where(
            or_(
                func.lower(ReferralPartner.name).like(search_filter),
                func.lower(ReferralPartner.phone).like(search_filter),
                func.lower(ReferralPartner.email).like(search_filter),
            )
        )

    count_query = select(func.count()).select_from(query.subquery())
    total_count = db.execute(count_query).scalar_one()

    query = (
        query.options(joinedload(ReferralPartner.rules))
        .order_by(ReferralPartner.created_at.desc())
        .limit(clamped_limit)
        .offset(clamped_offset)
    )

    partners = list(db.execute(query).scalars().unique().all())
    return partners, total_count


def update_referral_partner(
    db: Session,
    *,
    tenant_context: TenantContext,
    partner_id: str,
    name: str | None = None,
    partner_type: str | None = None,
    phone: str | None = None,
    email: str | None = None,
    status: str | None = None,
    actor_user_id: str | None = None,
) -> ReferralPartner:
    """Update referral partner details."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id
    effective_user_id = actor_user_id or tenant_context.user_id

    _enforce_user_permission(
        db,
        effective_user_id,
        tenant_id,
        "referral.rule.manage",
        tenant_context.branch_id,
    )

    partner = db.execute(
        select(ReferralPartner).where(
            ReferralPartner.tenant_id == tenant_id,
            ReferralPartner.id == partner_id,
        )
    ).scalars().first()

    if not partner:
        raise ReferralPartnerNotFoundError(f"Referral partner '{partner_id}' not found")

    before_json = {
        "name": partner.name,
        "partner_type": partner.partner_type,
        "phone": partner.phone,
        "email": partner.email,
        "status": partner.status,
    }

    if name is not None:
        clean_name = name.strip()
        if not clean_name:
            raise ValidationError("Referral partner name cannot be empty", field="name")
        partner.name = clean_name

    if partner_type is not None:
        raw_type = partner_type.strip().lower()
        if raw_type not in VALID_PARTNER_TYPES:
            raise ValidationError(f"Invalid partner_type '{partner_type}'", field="partner_type")
        partner.partner_type = CANONICAL_PARTNER_TYPES[raw_type]

    if phone is not None:
        partner.phone = phone.strip() if phone else None

    if email is not None:
        partner.email = email.strip().lower() if email else None

    if status is not None:
        clean_status = status.strip().lower()
        if clean_status not in VALID_STATUSES:
            raise ValidationError(f"Invalid status '{status}'", field="status")
        partner.status = clean_status

    log_audit_event(
        db,
        tenant_id=tenant_id,
        actor_user_id=effective_user_id,
        branch_id=tenant_context.branch_id,
        action_code="referral.partner.updated",
        entity_type="referral_partner",
        entity_id=partner.id,
        before_json=before_json,
        after_json={
            "name": partner.name,
            "partner_type": partner.partner_type,
            "phone": partner.phone,
            "email": partner.email,
            "status": partner.status,
        },
    )

    db.commit()
    db.refresh(partner)
    return partner



def create_referral_rule(
    db: Session,
    *,
    tenant_context: TenantContext,
    partner_id: str,
    scope_type: str = "all",
    scope_id: str | None = None,
    effective_from: datetime | None = None,
    effective_to: datetime | None = None,
    patient_discount_pct: float | Decimal = 0.0,
    commission_pct: float | Decimal = 0.0,
    commission_fixed: float | Decimal | None = None,
    priority: int = 100,
    status: str = "active",
    actor_user_id: str | None = None,
) -> ReferralRule:
    """Create a referral discount/commission rule for a referral partner."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id
    effective_user_id = actor_user_id or tenant_context.user_id

    _enforce_user_permission(
        db,
        effective_user_id,
        tenant_id,
        "referral.rule.manage",
        tenant_context.branch_id,
    )

    partner = db.execute(
        select(ReferralPartner).where(
            ReferralPartner.tenant_id == tenant_id,
            ReferralPartner.id == partner_id,
        )
    ).scalars().first()
    if not partner:
        raise ReferralPartnerNotFoundError(f"Referral partner '{partner_id}' not found")

    clean_scope = (scope_type or "all").strip().lower()
    if clean_scope not in VALID_SCOPE_TYPES:
        raise ValidationError(
            f"Invalid scope_type '{scope_type}'. Allowed scopes: {sorted(VALID_SCOPE_TYPES)}",
            field="scope_type",
        )
    if clean_scope != "all" and not scope_id:
        raise ValidationError(
            f"scope_id is required when scope_type is '{clean_scope}'",
            field="scope_id",
        )

    clean_disc = Decimal(str(patient_discount_pct))
    if clean_disc < Decimal("0.0") or clean_disc > Decimal("100.0"):
        raise ValidationError("patient_discount_pct must be between 0 and 100", field="patient_discount_pct")

    clean_comm_pct = Decimal(str(commission_pct))
    if clean_comm_pct < Decimal("0.0") or clean_comm_pct > Decimal("100.0"):
        raise ValidationError("commission_pct must be between 0 and 100", field="commission_pct")

    clean_comm_fix = Decimal(str(commission_fixed)) if commission_fixed is not None else None
    if clean_comm_fix is not None and clean_comm_fix < Decimal("0.0"):
        raise ValidationError("commission_fixed cannot be negative", field="commission_fixed")

    eff_from = effective_from or datetime.now(timezone.utc)
    if effective_to is not None and effective_to <= eff_from:
        raise ValidationError("effective_to must be after effective_from", field="effective_to")

    clean_status = (status or "active").strip().lower()
    if clean_status not in VALID_STATUSES:
        raise ValidationError(f"Invalid status '{status}'", field="status")

    rule = ReferralRule(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        partner_id=partner_id,
        scope_type=clean_scope,
        scope_id=scope_id,
        effective_from=eff_from,
        effective_to=effective_to,
        patient_discount_pct=float(clean_disc),
        commission_pct=float(clean_comm_pct),
        commission_fixed=float(clean_comm_fix) if clean_comm_fix is not None else None,
        priority=priority,
        status=clean_status,
        created_at=datetime.now(timezone.utc),
    )
    db.add(rule)
    db.flush()

    log_audit_event(
        db,
        tenant_id=tenant_id,
        actor_user_id=effective_user_id,
        branch_id=tenant_context.branch_id,
        action_code="referral.rule.created",
        entity_type="referral_rule",
        entity_id=rule.id,
        after_json={
            "rule_id": rule.id,
            "partner_id": rule.partner_id,
            "scope_type": rule.scope_type,
            "scope_id": rule.scope_id,
            "patient_discount_pct": float(clean_disc),
            "commission_pct": float(clean_comm_pct),
            "commission_fixed": float(clean_comm_fix) if clean_comm_fix is not None else None,
            "priority": rule.priority,
            "status": rule.status,
        },
    )

    db.commit()
    db.refresh(rule)
    return rule


def get_referral_rule(
    db: Session,
    *,
    tenant_context: TenantContext,
    rule_id: str,
    actor_user_id: str | None = None,
) -> ReferralRule:
    """Fetch referral rule by ID with tenant isolation."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    effective_user_id = actor_user_id or tenant_context.user_id

    _enforce_user_permission(
        db,
        effective_user_id,
        tenant_context.tenant_id,
        "referral.view",
        tenant_context.branch_id,
    )

    rule = db.execute(
        select(ReferralRule).where(
            ReferralRule.tenant_id == tenant_context.tenant_id,
            ReferralRule.id == rule_id,
        )
    ).scalars().first()

    if not rule:
        raise ReferralRuleNotFoundError(f"Referral rule '{rule_id}' not found")
    return rule



def list_referral_rules(
    db: Session,
    *,
    tenant_context: TenantContext,
    partner_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    actor_user_id: str | None = None,
) -> tuple[list[ReferralRule], int]:
    """List referral rules with tenant scoping and bounded pagination."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id
    effective_user_id = actor_user_id or tenant_context.user_id

    _enforce_user_permission(
        db,
        effective_user_id,
        tenant_id,
        "referral.view",
        tenant_context.branch_id,
    )

    clamped_limit = max(1, min(limit, 100))
    clamped_offset = max(0, offset)

    query = select(ReferralRule).where(ReferralRule.tenant_id == tenant_id)

    if partner_id:
        query = query.where(ReferralRule.partner_id == partner_id)

    if status:
        query = query.where(ReferralRule.status == status.strip().lower())

    count_query = select(func.count()).select_from(query.subquery())
    total_count = db.execute(count_query).scalar_one()

    query = (
        query.order_by(ReferralRule.priority.asc(), ReferralRule.created_at.desc())
        .limit(clamped_limit)
        .offset(clamped_offset)
    )

    rules = list(db.execute(query).scalars().all())
    return rules, total_count


def update_referral_rule(
    db: Session,
    *,
    tenant_context: TenantContext,
    rule_id: str,
    patient_discount_pct: float | Decimal | None = None,
    commission_pct: float | Decimal | None = None,
    commission_fixed: float | Decimal | None = None,
    priority: int | None = None,
    status: str | None = None,
    effective_to: datetime | None = None,
    actor_user_id: str | None = None,
) -> ReferralRule:
    """Update referral rule configuration."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id
    effective_user_id = actor_user_id or tenant_context.user_id

    _enforce_user_permission(
        db,
        effective_user_id,
        tenant_id,
        "referral.rule.manage",
        tenant_context.branch_id,
    )

    rule = db.execute(
        select(ReferralRule).where(
            ReferralRule.tenant_id == tenant_id,
            ReferralRule.id == rule_id,
        )
    ).scalars().first()

    if not rule:
        raise ReferralRuleNotFoundError(f"Referral rule '{rule_id}' not found")

    before_json = {
        "patient_discount_pct": float(rule.patient_discount_pct),
        "commission_pct": float(rule.commission_pct),
        "commission_fixed": float(rule.commission_fixed) if rule.commission_fixed is not None else None,
        "priority": rule.priority,
        "status": rule.status,
    }

    if patient_discount_pct is not None:
        disc = Decimal(str(patient_discount_pct))
        if disc < Decimal("0.0") or disc > Decimal("100.0"):
            raise ValidationError("patient_discount_pct must be between 0 and 100", field="patient_discount_pct")
        rule.patient_discount_pct = float(disc)

    if commission_pct is not None:
        comm = Decimal(str(commission_pct))
        if comm < Decimal("0.0") or comm > Decimal("100.0"):
            raise ValidationError("commission_pct must be between 0 and 100", field="commission_pct")
        rule.commission_pct = float(comm)

    if commission_fixed is not None:
        fixed = Decimal(str(commission_fixed))
        if fixed < Decimal("0.0"):
            raise ValidationError("commission_fixed cannot be negative", field="commission_fixed")
        rule.commission_fixed = float(fixed)

    if priority is not None:
        rule.priority = priority

    if status is not None:
        clean_status = status.strip().lower()
        if clean_status not in VALID_STATUSES:
            raise ValidationError(f"Invalid status '{status}'", field="status")
        rule.status = clean_status

    if effective_to is not None:
        if effective_to <= rule.effective_from:
            raise ValidationError("effective_to must be after effective_from", field="effective_to")
        rule.effective_to = effective_to

    log_audit_event(
        db,
        tenant_id=tenant_id,
        actor_user_id=effective_user_id,
        branch_id=tenant_context.branch_id,
        action_code="referral.rule.updated",
        entity_type="referral_rule",
        entity_id=rule.id,
        before_json=before_json,
        after_json={
            "patient_discount_pct": float(rule.patient_discount_pct),
            "commission_pct": float(rule.commission_pct),
            "commission_fixed": float(rule.commission_fixed) if rule.commission_fixed is not None else None,
            "priority": rule.priority,
            "status": rule.status,
        },
    )

    db.commit()
    db.refresh(rule)
    return rule


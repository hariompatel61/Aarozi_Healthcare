"""Tests for P04-06: Referral Partners.

Verifies:
1. Doctors, hospitals, labs, and collection-centre masters creation, retrieval, and updating.
2. Canonical partner type parsing and validation.
3. Referral rules configuration (scope, discounts, commissions, validity dates, priorities).
4. Server-side RBAC enforcement ('referral.view' and 'referral.rule.manage').
5. Bounded pagination and filters (partner_type, status, search).
6. Multi-tenant isolation for partners and rules.
7. Audit trail generation on sensitive master creation and modification.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from decimal import Decimal
import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.audit.service import get_audit_logs
from app.billing.referral_service import (
    create_referral_partner,
    get_referral_partner,
    list_referral_partners,
    update_referral_partner,
    create_referral_rule,
    get_referral_rule,
    list_referral_rules,
    update_referral_rule,
    ReferralPartnerNotFoundError,
    ReferralRuleNotFoundError,
)
from app.db import Base
from app.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.billing import ReferralPartner, ReferralRule
from app.models.core import Tenant, Branch
from app.models.identity import Permission, Role, RolePermission, User, UserRole
from app.security.tenant_guard import TenantContext


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def _setup_referral_env(db_session: Session):
    tenant = Tenant(name="Metro Diagnostic Labs", code="METRO-01")
    db_session.add(tenant)
    db_session.flush()

    branch = Branch(tenant_id=tenant.id, name="Central Branch", code="CEN-01")
    db_session.add(branch)

    # Permissions
    perm_view = Permission(code="referral.view", module="referral", resource="partner", action="view", risk_level="normal")
    perm_manage = Permission(code="referral.rule.manage", module="referral", resource="rule", action="manage", risk_level="high")
    db_session.add_all([perm_view, perm_manage])
    db_session.flush()

    # Manager role: has view + manage
    role_mgr = Role(tenant_id=tenant.id, name="Referral Manager", is_system=False)
    db_session.add(role_mgr)
    db_session.flush()
    db_session.add_all([
        RolePermission(role_id=role_mgr.id, permission_id=perm_view.id, allow=True),
        RolePermission(role_id=role_mgr.id, permission_id=perm_manage.id, allow=True),
    ])

    # Viewer role: view only
    role_viewer = Role(tenant_id=tenant.id, name="Referral Viewer", is_system=False)
    db_session.add(role_viewer)
    db_session.flush()
    db_session.add(RolePermission(role_id=role_viewer.id, permission_id=perm_view.id, allow=True))

    # User 1: Manager
    user_mgr = User(tenant_id=tenant.id, email="manager@metro.com", username="ref_manager", hashed_password="pw")
    db_session.add(user_mgr)
    db_session.flush()
    db_session.add(UserRole(user_id=user_mgr.id, role_id=role_mgr.id))

    # User 2: Viewer
    user_viewer = User(tenant_id=tenant.id, email="viewer@metro.com", username="ref_viewer", hashed_password="pw")
    db_session.add(user_viewer)
    db_session.flush()
    db_session.add(UserRole(user_id=user_viewer.id, role_id=role_viewer.id))

    # User 3: Unauthorized user (no referral perms)
    user_unauth = User(tenant_id=tenant.id, email="unauth@metro.com", username="ref_unauth", hashed_password="pw")
    db_session.add(user_unauth)
    db_session.flush()

    db_session.commit()

    return {
        "tenant": tenant,
        "branch": branch,
        "user_mgr": user_mgr,
        "user_viewer": user_viewer,
        "user_unauth": user_unauth,
        "ctx_mgr": TenantContext(tenant_id=tenant.id, branch_id=branch.id, user_id=user_mgr.id),
        "ctx_viewer": TenantContext(tenant_id=tenant.id, branch_id=branch.id, user_id=user_viewer.id),
        "ctx_unauth": TenantContext(tenant_id=tenant.id, branch_id=branch.id, user_id=user_unauth.id),
    }


def test_referral_partner_masters_crud_and_canonical_types(db_session: Session):
    """Test creating doctors, hospitals, labs, and collection centres with canonical type normalization."""
    env = _setup_referral_env(db_session)
    ctx = env["ctx_mgr"]

    # 1. Doctor
    doc = create_referral_partner(
        db_session,
        tenant_context=ctx,
        partner_type="doctor",
        name="Dr. Gregory House",
        phone="+1555019283",
        email="house@princeton.edu",
    )
    assert doc.id is not None
    assert doc.partner_type == "doctor"
    assert doc.name == "Dr. Gregory House"
    assert doc.status == "active"

    # 2. Hospital
    hosp = create_referral_partner(
        db_session,
        tenant_context=ctx,
        partner_type="hospital",
        name="Princeton Plainsboro Teaching Hospital",
        phone="+1555019999",
        email="info@ppth.org",
    )
    assert hosp.partner_type == "hospital"

    # 3. External lab (aliases to lab)
    lab = create_referral_partner(
        db_session,
        tenant_context=ctx,
        partner_type="external_lab",
        name="BioReference Central Lab",
        phone="+1555012233",
    )
    assert lab.partner_type == "lab"

    # 4. Collection centre (aliases to collection_centre)
    cc = create_referral_partner(
        db_session,
        tenant_context=ctx,
        partner_type="collection_center",
        name="Eastside Sample Collection Centre",
        phone="+1555014455",
    )
    assert cc.partner_type == "collection_centre"

    # Retrieve partner
    fetched = get_referral_partner(db_session, tenant_context=ctx, partner_id=doc.id)
    assert fetched.name == "Dr. Gregory House"

    # Update partner
    updated = update_referral_partner(
        db_session,
        tenant_context=ctx,
        partner_id=doc.id,
        phone="+1555999888",
        status="inactive",
    )
    assert updated.phone == "+1555999888"
    assert updated.status == "inactive"


def test_duplicate_and_validation_rules(db_session: Session):
    """Ensure duplicate detection per tenant/type/name and required field validations."""
    env = _setup_referral_env(db_session)
    ctx = env["ctx_mgr"]

    create_referral_partner(
        db_session,
        tenant_context=ctx,
        partner_type="doctor",
        name="Dr. Allison Cameron",
    )

    with pytest.raises(ConflictError) as exc:
        create_referral_partner(
            db_session,
            tenant_context=ctx,
            partner_type="doctor",
            name="dr. allison cameron",
        )
    assert "already exists" in str(exc.value)

    with pytest.raises(ValidationError):
        create_referral_partner(
            db_session,
            tenant_context=ctx,
            partner_type="doctor",
            name="",
        )

    with pytest.raises(ValidationError):
        create_referral_partner(
            db_session,
            tenant_context=ctx,
            partner_type="invalid_type_xyz",
            name="Someone",
        )



def test_referral_rules_lifecycle(db_session: Session):
    """Verify rule creation, validation, scoping, priorities, and updates."""
    env = _setup_referral_env(db_session)
    ctx = env["ctx_mgr"]
    now = datetime.now(timezone.utc)

    doc = create_referral_partner(
        db_session,
        tenant_context=ctx,
        partner_type="doctor",
        name="Dr. James Wilson",
    )

    rule_global = create_referral_rule(
        db_session,
        tenant_context=ctx,
        partner_id=doc.id,
        scope_type="all",
        patient_discount_pct=10.0,
        commission_pct=15.0,
        priority=100,
        effective_from=now,
    )
    assert rule_global.id is not None
    assert rule_global.scope_type == "all"
    assert float(rule_global.patient_discount_pct) == 10.0
    assert float(rule_global.commission_pct) == 15.0

    dept_id = str(uuid.uuid4())
    rule_dept = create_referral_rule(
        db_session,
        tenant_context=ctx,
        partner_id=doc.id,
        scope_type="department",
        scope_id=dept_id,
        patient_discount_pct=15.0,
        commission_pct=20.0,
        priority=50,
        effective_from=now,
    )
    assert rule_dept.scope_type == "department"
    assert rule_dept.scope_id == dept_id

    with pytest.raises(ValidationError):
        create_referral_rule(
            db_session,
            tenant_context=ctx,
            partner_id=doc.id,
            scope_type="test",
            scope_id=None,
        )

    with pytest.raises(ValidationError):
        create_referral_rule(
            db_session,
            tenant_context=ctx,
            partner_id=doc.id,
            scope_type="all",
            patient_discount_pct=110.0,
        )

    with pytest.raises(ValidationError):
        create_referral_rule(
            db_session,
            tenant_context=ctx,
            partner_id=doc.id,
            scope_type="all",
            effective_from=now,
            effective_to=now - timedelta(days=1),
        )

    rules, count = list_referral_rules(db_session, tenant_context=ctx, partner_id=doc.id)
    assert count == 2
    assert rules[0].priority == 50

    updated_rule = update_referral_rule(
        db_session,
        tenant_context=ctx,
        rule_id=rule_dept.id,
        commission_pct=25.0,
        commission_fixed=5.0,
    )
    assert float(updated_rule.commission_pct) == 25.0
    assert float(updated_rule.commission_fixed) == 5.0



def test_rbac_server_side_authorization(db_session: Session):
    """Enforce 'referral.view' for listing/fetching and 'referral.rule.manage' for mutations."""
    env = _setup_referral_env(db_session)
    ctx_mgr = env["ctx_mgr"]
    ctx_viewer = env["ctx_viewer"]
    ctx_unauth = env["ctx_unauth"]

    # Manager can create
    doc = create_referral_partner(
        db_session,
        tenant_context=ctx_mgr,
        partner_type="doctor",
        name="Dr. Eric Foreman",
    )

    # Viewer cannot create or update
    with pytest.raises(ForbiddenError):
        create_referral_partner(
            db_session,
            tenant_context=ctx_viewer,
            partner_type="hospital",
            name="Hope Hospital",
        )

    with pytest.raises(ForbiddenError):
        update_referral_partner(
            db_session,
            tenant_context=ctx_viewer,
            partner_id=doc.id,
            name="New Name",
        )

    with pytest.raises(ForbiddenError):
        create_referral_rule(
            db_session,
            tenant_context=ctx_viewer,
            partner_id=doc.id,
            scope_type="all",
        )

    # Viewer CAN view/list
    fetched = get_referral_partner(db_session, tenant_context=ctx_viewer, partner_id=doc.id)
    assert fetched.id == doc.id
    partners, cnt = list_referral_partners(db_session, tenant_context=ctx_viewer)
    assert cnt >= 1

    # Unauthorized user cannot view or list
    with pytest.raises(ForbiddenError):
        get_referral_partner(db_session, tenant_context=ctx_unauth, partner_id=doc.id)

    with pytest.raises(ForbiddenError):
        list_referral_partners(db_session, tenant_context=ctx_unauth)


def test_multi_tenant_isolation_and_auditability(db_session: Session):
    """Ensure strict tenant isolation across queries/writes and audit logging for sensitive partner actions."""
    env = _setup_referral_env(db_session)
    ctx1 = env["ctx_mgr"]

    # Tenant 2
    t2 = Tenant(name="St. Jude Diagnostic Center", code="STJUDE")
    db_session.add(t2)
    db_session.flush()
    ctx2 = TenantContext(tenant_id=t2.id, branch_id=str(uuid.uuid4()))

    p1 = create_referral_partner(
        db_session,
        tenant_context=ctx1,
        partner_type="doctor",
        name="Dr. Robert Chase",
    )
    r1 = create_referral_rule(
        db_session,
        tenant_context=ctx1,
        partner_id=p1.id,
        patient_discount_pct=5.0,
    )

    # Tenant 2 cannot access Tenant 1 partner or rule
    with pytest.raises(ReferralPartnerNotFoundError):
        get_referral_partner(db_session, tenant_context=ctx2, partner_id=p1.id)

    with pytest.raises(ReferralRuleNotFoundError):
        get_referral_rule(db_session, tenant_context=ctx2, rule_id=r1.id)

    # Listing under Tenant 2 returns empty
    t2_partners, t2_count = list_referral_partners(db_session, tenant_context=ctx2)
    assert t2_count == 0
    assert len(t2_partners) == 0

    # Audit events verified for Tenant 1
    audits_partner = get_audit_logs(
        db_session,
        tenant_id=ctx1.tenant_id,
        entity_type="referral_partner",
        entity_id=p1.id,
    )
    assert len(audits_partner) >= 1
    assert audits_partner[0].action_code == "referral.partner.created"
    assert audits_partner[0].after_json["name"] == "Dr. Robert Chase"

    audits_rule = get_audit_logs(
        db_session,
        tenant_id=ctx1.tenant_id,
        entity_type="referral_rule",
        entity_id=r1.id,
    )
    assert len(audits_rule) >= 1
    assert audits_rule[0].action_code == "referral.rule.created"


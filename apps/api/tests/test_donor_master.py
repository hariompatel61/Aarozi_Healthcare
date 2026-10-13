"""Tests for P07-01: Donor Master (Identity, History, Deferral Model, Eligibility, RBAC)."""
import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.audit.service import get_audit_logs
from app.blood_bank.donor_service import (
    check_donor_eligibility,
    defer_donor,
    get_donor,
    lift_deferral,
    list_donors,
    register_donor,
)
from app.db import Base
from app.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.blood_bank import Donor, DonorDeferral
from app.models.core import Branch, Tenant
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


def _setup_donor_env(db: Session):
    t1 = Tenant(name="City Blood Center", code="CBC-01", is_active=True)
    t2 = Tenant(name="Regional Blood Bank", code="RBB-02", is_active=True)
    db.add_all([t1, t2])
    db.flush()

    b1 = Branch(tenant_id=t1.id, name="Main Blood Bank", code="MBB-01", is_active=True)
    b2 = Branch(tenant_id=t2.id, name="Regional Center", code="RC-01", is_active=True)
    db.add_all([b1, b2])
    db.flush()

    perms = [
        Permission(code="blood.donor.create", module="blood_bank", resource="donor", action="create", risk_level="normal"),
        Permission(code="blood.donor.screen", module="blood_bank", resource="donor", action="screen", risk_level="high"),
    ]
    db.add_all(perms)
    db.flush()

    role_officer = Role(tenant_id=t1.id, name="Blood Bank Officer", is_system=False)
    role_ro = Role(tenant_id=t1.id, name="Read Only", is_system=False)
    db.add_all([role_officer, role_ro])
    db.flush()

    for p in perms:
        db.add(RolePermission(role_id=role_officer.id, permission_id=p.id, allow=True))

    user_officer = User(tenant_id=t1.id, email="officer@cbc.com", username="bb_officer", hashed_password="pw")
    user_ro = User(tenant_id=t1.id, email="ro@cbc.com", username="ro_user", hashed_password="pw")
    db.add_all([user_officer, user_ro])
    db.flush()

    db.add_all([
        UserRole(user_id=user_officer.id, role_id=role_officer.id),
        UserRole(user_id=user_ro.id, role_id=role_ro.id),
    ])

    ctx_officer = TenantContext(tenant_id=t1.id, branch_id=b1.id, user_id=user_officer.id)
    ctx_ro = TenantContext(tenant_id=t1.id, branch_id=b1.id, user_id=user_ro.id)
    ctx2 = TenantContext(tenant_id=t2.id, branch_id=b2.id, user_id=str(uuid.uuid4()))

    db.commit()

    return {
        "ctx_officer": ctx_officer,
        "ctx_ro": ctx_ro,
        "ctx2": ctx2,
    }


def test_donor_registration_lifecycle_and_validation(db_session: Session):
    env = _setup_donor_env(db_session)
    ctx_officer = env["ctx_officer"]
    ctx_ro = env["ctx_ro"]

    # 1. Successful donor registration
    donor = register_donor(
        db_session,
        tenant_context=ctx_officer,
        first_name="Alexander",
        last_name="Fleming",
        sex="male",
        date_of_birth=date(1990, 8, 6),
        blood_group="O+",
        mobile="+15551112222",
        national_id="NAT-FL-9910",
    )
    assert donor.id is not None
    assert donor.donor_no.startswith("DNR-")
    assert donor.blood_group == "O_POS"
    assert donor.status == "active"

    # Audit log check
    logs = get_audit_logs(db_session, tenant_id=ctx_officer.tenant_id, entity_type="donor", entity_id=donor.id)
    assert any(l.action_code == "blood.donor.created" for l in logs)

    # 2. Duplicate national ID rejected
    with pytest.raises(ConflictError):
        register_donor(
            db_session,
            tenant_context=ctx_officer,
            first_name="Alex",
            sex="male",
            date_of_birth=date(1990, 8, 6),
            national_id="NAT-FL-9910",
        )

    # 3. Underage donor (< 18 yrs) rejected
    with pytest.raises(ValidationError):
        register_donor(
            db_session,
            tenant_context=ctx_officer,
            first_name="Young",
            sex="male",
            date_of_birth=date(2015, 1, 1),
        )

    # 4. RBAC: User without blood.donor.create permission is blocked
    with pytest.raises(ForbiddenError):
        register_donor(
            db_session,
            tenant_context=ctx_ro,
            first_name="Blocked",
            sex="female",
        )


def test_donor_deferral_and_lifting_lifecycle(db_session: Session):
    env = _setup_donor_env(db_session)
    ctx = env["ctx_officer"]

    donor = register_donor(
        db_session,
        tenant_context=ctx,
        first_name="Louis",
        last_name="Pasteur",
        sex="male",
        date_of_birth=date(1985, 12, 27),
        blood_group="A-",
    )

    # 1. Initial eligibility check: Eligible
    elig_1 = check_donor_eligibility(db_session, tenant_context=ctx, donor_id=donor.id)
    assert elig_1["is_eligible"] is True
    assert elig_1["status"] == "eligible"

    # 2. Apply temporary deferral (e.g. low hemoglobin, deferred for 30 days)
    defer_date = datetime.now(timezone.utc) + timedelta(days=30)
    deferral = defer_donor(
        db_session,
        tenant_context=ctx,
        donor_id=donor.id,
        deferral_type="temporary",
        reason="Hemoglobin 11.4 g/dL below acceptable threshold (12.5 required)",
        deferred_until=defer_date,
    )
    db_session.refresh(donor)
    assert donor.status == "deferred_temporary"

    # Eligibility check: Not eligible due to temporary deferral
    elig_2 = check_donor_eligibility(db_session, tenant_context=ctx, donor_id=donor.id)
    assert elig_2["is_eligible"] is False
    assert elig_2["status"] == "deferred_temporary"
    assert "Hemoglobin" in elig_2["reason"]

    # 3. Lift deferral after re-testing Hb
    lifted = lift_deferral(
        db_session,
        tenant_context=ctx,
        deferral_id=deferral.id,
        lift_reason="Repeat capillary Hb measured 13.2 g/dL following dietary iron therapy",
    )
    assert lifted.status == "lifted"
    db_session.refresh(donor)
    assert donor.status == "active"

    # Eligibility check after lift: Eligible
    elig_3 = check_donor_eligibility(db_session, tenant_context=ctx, donor_id=donor.id)
    assert elig_3["is_eligible"] is True

    # 4. Permanent deferral (e.g. Reactive viral marker)
    perm_def = defer_donor(
        db_session,
        tenant_context=ctx,
        donor_id=donor.id,
        deferral_type="permanent",
        reason="Confirmed reactive for Hepatitis B surface antigen",
    )
    db_session.refresh(donor)
    assert donor.status == "deferred_permanent"

    elig_4 = check_donor_eligibility(db_session, tenant_context=ctx, donor_id=donor.id)
    assert elig_4["is_eligible"] is False
    assert elig_4["status"] == "deferred_permanent"

    # Permanent deferral cannot be routinely lifted
    with pytest.raises(ConflictError):
        lift_deferral(db_session, tenant_context=ctx, deferral_id=perm_def.id, lift_reason="Test")


def test_donation_interval_rule_and_tenant_isolation(db_session: Session):
    env = _setup_donor_env(db_session)
    ctx1 = env["ctx_officer"]
    ctx2 = env["ctx2"]

    donor = register_donor(
        db_session,
        tenant_context=ctx1,
        first_name="Jonas",
        last_name="Salk",
        sex="male",
        date_of_birth=date(1980, 10, 28),
    )

    # Simulate recent donation 20 days ago (minimum interval is 56 days)
    donor.last_donation_date = datetime.now(timezone.utc) - timedelta(days=20)
    db_session.commit()

    elig = check_donor_eligibility(db_session, tenant_context=ctx1, donor_id=donor.id, donation_type="whole_blood")
    assert elig["is_eligible"] is False
    assert elig["status"] == "interval_not_met"
    assert elig["days_until_eligible"] in (36, 37)

    # Multi-tenant isolation: Tenant 2 cannot see or access Tenant 1 donor
    with pytest.raises(NotFoundError):
        get_donor(db_session, tenant_context=ctx2, donor_id=donor.id)

    donors_t2, count_t2 = list_donors(db_session, tenant_context=ctx2)
    assert count_t2 == 0
    assert len(donors_t2) == 0


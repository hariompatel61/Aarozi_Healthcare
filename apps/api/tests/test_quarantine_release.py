"""Tests for Blood Bank Quarantine, Release & Discard (P07-06)."""
import uuid
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.blood_bank.donation_service import record_donation
from app.blood_bank.donor_service import register_donor
from app.blood_bank.testing_service import record_blood_unit_tests, verify_blood_unit_test
from app.blood_bank.quarantine_service import quarantine_unit, release_unit, discard_unit
from app.db import Base
from app.errors import ConflictError, ValidationError
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


def _setup_qr_env(db: Session):
    t1 = Tenant(id=str(uuid.uuid4()), name="Alpha BB", code=f"ABB_{uuid.uuid4().hex[:6]}")
    db.add(t1)
    db.flush()

    b1 = Branch(id=str(uuid.uuid4()), tenant_id=t1.id, name="Main Alpha", code="MA")
    db.add(b1)
    db.flush()

    perms = [
        Permission(code="blood.donor.create", module="blood_bank", resource="donor", action="create", risk_level="normal"),
        Permission(code="blood.unit.receive", module="blood_bank", resource="unit", action="receive", risk_level="normal"),
    ]
    db.add_all(perms)
    db.flush()

    role = Role(tenant_id=t1.id, name="BB Officer", is_system=False)
    db.add(role)
    db.flush()

    for p in perms:
        db.add(RolePermission(role_id=role.id, permission_id=p.id, allow=True))

    user = User(tenant_id=t1.id, email="officer@alpha.org", username="alpha_officer", hashed_password="pw")
    db.add(user)
    db.flush()

    db.add(UserRole(user_id=user.id, role_id=role.id))

    ctx = TenantContext(tenant_id=t1.id, branch_id=b1.id, user_id=user.id)
    db.commit()
    return {"ctx": ctx}


def test_release_requires_tti_clearance(db_session: Session):
    env = _setup_qr_env(db_session)
    ctx = env["ctx"]

    donor = register_donor(
        db_session,
        tenant_context=ctx,
        first_name="Peter",
        last_name="Parker",
        sex="male",
        blood_group="O_POS",
    )

    donation = record_donation(
        db_session,
        tenant_context=ctx,
        donor_id=donor.id,
        bag_type="single",
        volume_ml=450,
        status="completed",
    )

    unit = donation.blood_units[0]

    # Trying to release without testing clearance should raise ConflictError
    with pytest.raises(ConflictError):
        release_unit(db_session, tenant_context=ctx, blood_unit_id=unit.id)

    # Record and verify TTI tests
    tests_input = [
        {"test_code": "HIV", "result": "negative"},
        {"test_code": "HBSAG", "result": "negative"},
        {"test_code": "HCV", "result": "negative"},
        {"test_code": "VDRL", "result": "non_reactive"},
        {"test_code": "MALARIA", "result": "negative"},
    ]
    recorded = record_blood_unit_tests(
        db_session,
        tenant_context=ctx,
        blood_unit_id=unit.id,
        tests_input=tests_input,
    )
    for t in recorded:
        verify_blood_unit_test(db_session, tenant_context=ctx, test_id=t.id, result="negative")

    # Now release should succeed
    released = release_unit(db_session, tenant_context=ctx, blood_unit_id=unit.id)
    assert released.status == "released"


def test_quarantine_and_discard(db_session: Session):
    env = _setup_qr_env(db_session)
    ctx = env["ctx"]

    donor = register_donor(
        db_session,
        tenant_context=ctx,
        first_name="Mary",
        last_name="Jane",
        sex="female",
        blood_group="A_NEG",
    )

    donation = record_donation(
        db_session,
        tenant_context=ctx,
        donor_id=donor.id,
        bag_type="single",
        volume_ml=450,
        status="completed",
    )

    unit = donation.blood_units[0]

    quarantined = quarantine_unit(db_session, tenant_context=ctx, blood_unit_id=unit.id, reason="Lipemic sample")
    assert quarantined.status == "quarantined"

    discarded = discard_unit(db_session, tenant_context=ctx, blood_unit_id=unit.id, reason="Bag damaged during handling")
    assert discarded.status == "discarded"

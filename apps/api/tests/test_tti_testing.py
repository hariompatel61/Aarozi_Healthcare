"""Tests for Blood Bank TTI & Component Testing (P07-05)."""
import uuid
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.blood_bank.donation_service import record_donation
from app.blood_bank.donor_service import register_donor
from app.blood_bank.testing_service import (
    record_blood_unit_tests,
    verify_blood_unit_test,
    list_blood_unit_tests,
    check_unit_testing_clearance,
)
from app.db import Base
from app.errors import NotFoundError, ConflictError
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


def _setup_testing_env(db: Session):
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

    role = Role(tenant_id=t1.id, name="Testing Officer", is_system=False)
    db.add(role)
    db.flush()

    for p in perms:
        db.add(RolePermission(role_id=role.id, permission_id=p.id, allow=True))

    user = User(tenant_id=t1.id, email="tester@alpha.org", username="alpha_tester", hashed_password="pw")
    db.add(user)
    db.flush()

    db.add(UserRole(user_id=user.id, role_id=role.id))

    ctx = TenantContext(tenant_id=t1.id, branch_id=b1.id, user_id=user.id)
    db.commit()
    return {"ctx": ctx, "user": user}


def test_tti_testing_workflow_and_clearance(db_session: Session):
    env = _setup_testing_env(db_session)
    ctx = env["ctx"]

    donor = register_donor(
        db_session,
        tenant_context=ctx,
        first_name="Oliver",
        last_name="Queen",
        sex="male",
        blood_group="B_POS",
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
    assert unit.status == "collected"

    # Record TTI tests
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
    assert len(recorded) == 5
    assert unit.status == "testing"

    # Initially clearance is not achieved because status is 'pending'
    clearance = check_unit_testing_clearance(db_session, tenant_context=ctx, blood_unit_id=unit.id)
    assert clearance["cleared"] is False
    assert len(clearance["pending"]) == 5

    # Verify all tests
    for t in recorded:
        verify_blood_unit_test(
            db_session,
            tenant_context=ctx,
            test_id=t.id,
            result="negative",
        )

    # Now clearance should be True
    clearance_after = check_unit_testing_clearance(db_session, tenant_context=ctx, blood_unit_id=unit.id)
    assert clearance_after["cleared"] is True
    assert len(clearance_after["pending"]) == 0
    assert len(clearance_after["reactive"]) == 0

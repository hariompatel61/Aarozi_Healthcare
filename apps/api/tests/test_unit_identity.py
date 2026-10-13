"""Tests for Blood Bank Unit Identity, Barcode & Traceability (P07-04)."""
import uuid
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.blood_bank.donation_service import record_donation
from app.blood_bank.donor_service import register_donor
from app.blood_bank.unit_service import (
    get_blood_unit_by_barcode,
    update_unit_status,
    get_unit_traceability,
    log_blood_movement,
)
from app.db import Base
from app.errors import NotFoundError, ForbiddenError
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


def _setup_unit_env(db: Session):
    t1 = Tenant(id=str(uuid.uuid4()), name="Alpha BB", code=f"ABB_{uuid.uuid4().hex[:6]}")
    t2 = Tenant(id=str(uuid.uuid4()), name="Beta BB", code=f"BBB_{uuid.uuid4().hex[:6]}")
    db.add_all([t1, t2])
    db.flush()

    b1 = Branch(id=str(uuid.uuid4()), tenant_id=t1.id, name="Main Alpha", code="MA")
    b2 = Branch(id=str(uuid.uuid4()), tenant_id=t2.id, name="Main Beta", code="MB")
    db.add_all([b1, b2])
    db.flush()

    perms = [
        Permission(code="blood.donor.create", module="blood_bank", resource="donor", action="create", risk_level="normal"),
        Permission(code="blood.unit.receive", module="blood_bank", resource="unit", action="receive", risk_level="normal"),
        Permission(code="blood.unit.issue", module="blood_bank", resource="unit", action="issue", risk_level="high"),
    ]
    db.add_all(perms)
    db.flush()

    role = Role(tenant_id=t1.id, name="Blood Bank Officer", is_system=False)
    db.add(role)
    db.flush()

    for p in perms:
        db.add(RolePermission(role_id=role.id, permission_id=p.id, allow=True))

    user = User(tenant_id=t1.id, email="officer@alpha.org", username="alpha_officer", hashed_password="pw")
    db.add(user)
    db.flush()

    db.add(UserRole(user_id=user.id, role_id=role.id))

    ctx = TenantContext(tenant_id=t1.id, branch_id=b1.id, user_id=user.id)
    ctx2 = TenantContext(tenant_id=t2.id, branch_id=b2.id, user_id=user.id)

    db.commit()
    return {"ctx": ctx, "ctx2": ctx2}


def test_unit_barcode_lookup_and_traceability(db_session: Session):
    env = _setup_unit_env(db_session)
    ctx = env["ctx"]

    donor = register_donor(
        db_session,
        tenant_context=ctx,
        first_name="John",
        last_name="Doe",
        sex="male",
        blood_group="A_POS",
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
    unit_no = unit.unit_no

    # Test barcode lookup
    found_unit = get_blood_unit_by_barcode(db_session, tenant_context=ctx, unit_no=unit_no)
    assert found_unit.id == unit.id
    assert found_unit.blood_group == "A_POS"
    assert found_unit.status == "collected"

    # Test status update & movement logging
    updated_unit = update_unit_status(
        db_session,
        tenant_context=ctx,
        blood_unit_id=unit.id,
        new_status="testing",
        movement_type="sample_testing",
        reason="Testing for TTI",
    )
    assert updated_unit.status == "testing"

    # Test traceability
    trace = get_unit_traceability(db_session, tenant_context=ctx, blood_unit_id=unit.id)
    assert trace["unit"].id == unit.id
    assert trace["donation"].id == donation.id
    assert trace["donor"].id == donor.id
    assert len(trace["movements"]) == 1
    mov = trace["movements"][0]
    assert mov.from_status == "collected"
    assert mov.to_status == "testing"
    assert mov.movement_type == "sample_testing"
    assert mov.reason == "Testing for TTI"


def test_unit_tenant_isolation(db_session: Session):
    env = _setup_unit_env(db_session)
    ctx = env["ctx"]
    ctx2 = env["ctx2"]

    donor = register_donor(
        db_session,
        tenant_context=ctx,
        first_name="Jane",
        last_name="Smith",
        sex="female",
        blood_group="O_NEG",
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

    # Tenant 2 cannot lookup tenant 1's blood unit
    with pytest.raises(NotFoundError):
        get_blood_unit_by_barcode(db_session, tenant_context=ctx2, unit_no=unit.unit_no)


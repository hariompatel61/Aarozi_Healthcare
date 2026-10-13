"""Tests for Blood Bank Reservations, Cross-Match, Issue/Return & Adverse Events (P07-08 to P07-11)."""
import uuid
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.blood_bank.donation_service import record_donation
from app.blood_bank.donor_service import register_donor
from app.blood_bank.testing_service import record_blood_unit_tests, verify_blood_unit_test
from app.blood_bank.quarantine_service import release_unit
from app.blood_bank.transfusion_service import (
    reserve_unit,
    perform_cross_match,
    approve_cross_match,
    issue_unit,
    return_unit,
    record_adverse_event,
)
from app.db import Base
from app.errors import ConflictError, ValidationError
from app.models.core import Branch, Tenant
from app.models.identity import Permission, Role, RolePermission, User, UserRole
from app.models.patient import Patient
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


def _setup_transfusion_env(db: Session):
    t1 = Tenant(id=str(uuid.uuid4()), name="Alpha BB", code=f"ABB_{uuid.uuid4().hex[:6]}")
    db.add(t1)
    db.flush()

    b1 = Branch(id=str(uuid.uuid4()), tenant_id=t1.id, name="Main Alpha", code="MA")
    db.add(b1)
    db.flush()

    perms = [
        Permission(code="blood.donor.create", module="blood_bank", resource="donor", action="create", risk_level="normal"),
        Permission(code="blood.unit.receive", module="blood_bank", resource="unit", action="receive", risk_level="normal"),
        Permission(code="blood.unit.issue", module="blood_bank", resource="unit", action="issue", risk_level="high"),
    ]
    db.add_all(perms)
    db.flush()

    role = Role(tenant_id=t1.id, name="BB Transfusion Officer", is_system=False)
    db.add(role)
    db.flush()

    for p in perms:
        db.add(RolePermission(role_id=role.id, permission_id=p.id, allow=True))

    user = User(tenant_id=t1.id, email="transfusion@alpha.org", username="alpha_transfusion", hashed_password="pw")
    db.add(user)
    db.flush()

    db.add(UserRole(user_id=user.id, role_id=role.id))

    patient = Patient(tenant_id=t1.id, patient_no="P1001", first_name="Clark", last_name="Kent", sex="male", date_of_birth=date(1980, 6, 18))
    db.add(patient)
    db.flush()

    ctx = TenantContext(tenant_id=t1.id, branch_id=b1.id, user_id=user.id)
    db.commit()
    return {"ctx": ctx, "patient": patient}


def test_transfusion_workflow_reservation_crossmatch_issue_return_adverse(db_session: Session):
    env = _setup_transfusion_env(db_session)
    ctx = env["ctx"]
    patient = env["patient"]

    donor = register_donor(
        db_session,
        tenant_context=ctx,
        first_name="Lois",
        last_name="Lane",
        sex="female",
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

    # Test and release unit
    tests_input = [
        {"test_code": "HIV", "result": "negative"},
        {"test_code": "HBSAG", "result": "negative"},
        {"test_code": "HCV", "result": "negative"},
        {"test_code": "VDRL", "result": "non_reactive"},
        {"test_code": "MALARIA", "result": "negative"},
    ]
    recorded = record_blood_unit_tests(db_session, tenant_context=ctx, blood_unit_id=unit.id, tests_input=tests_input)
    for t in recorded:
        verify_blood_unit_test(db_session, tenant_context=ctx, test_id=t.id, result="negative")
    release_unit(db_session, tenant_context=ctx, blood_unit_id=unit.id)

    # 1. Reserve unit (P07-08)
    reserved = reserve_unit(db_session, tenant_context=ctx, blood_unit_id=unit.id, patient_id=patient.id)
    assert reserved.status == "reserved"

    # 2. Cross-match (P07-09)
    cm = perform_cross_match(db_session, tenant_context=ctx, patient_id=patient.id, blood_unit_id=unit.id)
    assert cm.compatibility_status == "pending"
    approved_cm = approve_cross_match(db_session, tenant_context=ctx, cross_match_id=cm.id, compatibility_status="compatible")
    assert approved_cm.compatibility_status == "compatible"

    # 3. Issue unit (P07-10)
    issued = issue_unit(db_session, tenant_context=ctx, blood_unit_id=unit.id, patient_id=patient.id)
    assert issued.status == "issued"

    # 4. Adverse Event (P07-11)
    ae = record_adverse_event(
        db_session,
        tenant_context=ctx,
        blood_unit_id=unit.id,
        patient_id=patient.id,
        reaction_type="febrile_non_hemolytic",
        severity="mild",
        symptoms="Chills and mild fever",
        action_taken="Slowed transfusion and administered antipyretic",
    )
    assert ae.id is not None
    assert ae.reaction_type == "febrile_non_hemolytic"

    # 5. Return unit (P07-10)
    returned = return_unit(db_session, tenant_context=ctx, blood_unit_id=unit.id, reason="Transfusion halted due to mild reaction")
    assert returned.status == "released"

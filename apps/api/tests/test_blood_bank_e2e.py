"""End-to-End Tests for Blood Bank & Transfusion Medicine (P07-12)."""
import uuid
from datetime import date
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.blood_bank.donor_service import register_donor
from app.blood_bank.screening_service import conduct_screening
from app.blood_bank.donation_service import record_donation
from app.blood_bank.unit_service import get_blood_unit_by_barcode, get_unit_traceability
from app.blood_bank.testing_service import record_blood_unit_tests, verify_blood_unit_test
from app.blood_bank.quarantine_service import release_unit
from app.blood_bank.inventory_service import get_blood_inventory
from app.blood_bank.transfusion_service import (
    reserve_unit, perform_cross_match, approve_cross_match,
    issue_unit, return_unit, record_adverse_event
)
from app.db import Base
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


def test_complete_blood_bank_e2e_pipeline(db_session: Session):
    t1 = Tenant(id=str(uuid.uuid4()), name="BB", code=f"BB_{uuid.uuid4().hex[:4]}")
    db_session.add(t1)
    db_session.flush()
    b1 = Branch(id=str(uuid.uuid4()), tenant_id=t1.id, name="B", code="B1")
    db_session.add(b1)
    db_session.flush()

    perms = [
        Permission(code="blood.donor.create", module="blood_bank", resource="donor", action="create", risk_level="normal"),
        Permission(code="blood.donor.screen", module="blood_bank", resource="donor", action="screen", risk_level="high"),
        Permission(code="blood.unit.receive", module="blood_bank", resource="unit", action="receive", risk_level="normal"),
        Permission(code="blood.unit.issue", module="blood_bank", resource="unit", action="issue", risk_level="high"),
    ]
    db_session.add_all(perms)
    db_session.flush()

    role = Role(tenant_id=t1.id, name="Sup", is_system=False)
    db_session.add(role)
    db_session.flush()
    for p in perms:
        db_session.add(RolePermission(role_id=role.id, permission_id=p.id, allow=True))

    user = User(tenant_id=t1.id, email="s@bb.org", username="sup", hashed_password="pw")
    db_session.add(user)
    db_session.flush()
    db_session.add(UserRole(user_id=user.id, role_id=role.id))

    patient = Patient(
        tenant_id=t1.id, patient_no="P001", first_name="Rec", last_name="Pat",
        sex="female", date_of_birth=date(1992, 5, 10), blood_group="A_POS"
    )
    db_session.add(patient)
    db_session.commit()

    ctx = TenantContext(tenant_id=t1.id, branch_id=b1.id, user_id=user.id)

    donor = register_donor(
        db_session, tenant_context=ctx, first_name="Gen", last_name="Don",
        sex="male", date_of_birth=date(1990, 1, 1), blood_group="A_POS", mobile="9876543210"
    )
    assert donor.donor_no is not None

    screening = conduct_screening(
        db_session, tenant_context=ctx, donor_id=donor.id,
        weight_kg=75.0, hemoglobin_g_dl=14.5, temperature_c=36.5,
        blood_pressure_systolic=120, blood_pressure_diastolic=80, pulse_bpm=72,
        questionnaire_responses={"feeling_well": True}
    )
    assert screening.status == "passed"

    donation = record_donation(
        db_session, tenant_context=ctx, donor_id=donor.id, bag_type="triple",
        volume_ml=450, venipuncture_site="left_antecubital", status="completed"
    )
    assert len(donation.blood_units) == 3

    prbc = [u for u in donation.blood_units if u.component_type == "packed_red_cells"][0]
    fetched = get_blood_unit_by_barcode(db_session, tenant_context=ctx, unit_no=prbc.unit_no)
    assert fetched.id == prbc.id

    trace = get_unit_traceability(db_session, tenant_context=ctx, blood_unit_id=prbc.id)
    assert trace["donor"].id == donor.id

    tests_input = [
        {"test_code": "HIV", "result": "negative"},
        {"test_code": "HBSAG", "result": "negative"},
        {"test_code": "HCV", "result": "negative"},
        {"test_code": "VDRL", "result": "non_reactive"},
        {"test_code": "MALARIA", "result": "negative"},
    ]
    recorded = record_blood_unit_tests(db_session, tenant_context=ctx, blood_unit_id=prbc.id, tests_input=tests_input)
    for t in recorded:
        verify_blood_unit_test(db_session, tenant_context=ctx, test_id=t.id, result="negative")

    released = release_unit(db_session, tenant_context=ctx, blood_unit_id=prbc.id)
    assert released.status == "released"

    inv = get_blood_inventory(db_session, tenant_context=ctx, blood_group="A_POS", component_type="packed_red_cells")
    assert len(inv) == 1

    reserved = reserve_unit(db_session, tenant_context=ctx, blood_unit_id=prbc.id, patient_id=patient.id)
    assert reserved.status == "reserved"

    cm = perform_cross_match(db_session, tenant_context=ctx, patient_id=patient.id, blood_unit_id=prbc.id)
    app_cm = approve_cross_match(db_session, tenant_context=ctx, cross_match_id=cm.id, compatibility_status="compatible")
    assert app_cm.compatibility_status == "compatible"

    issued = issue_unit(db_session, tenant_context=ctx, blood_unit_id=prbc.id, patient_id=patient.id)
    assert issued.status == "issued"

    ae = record_adverse_event(
        db_session, tenant_context=ctx, blood_unit_id=prbc.id, patient_id=patient.id,
        reaction_type="urticarial", severity="mild", symptoms="Itching", action_taken="Antihistamine"
    )
    assert ae.reaction_type == "urticarial"

    returned = return_unit(db_session, tenant_context=ctx, blood_unit_id=prbc.id, reason="Stopped safely")
    assert returned.status == "released"

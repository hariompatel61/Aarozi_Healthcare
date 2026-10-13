"""Tests for Blood Bank Donation Records & Component Generation (P07-03)."""
import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.blood_bank.donation_service import (
    calculate_component_expiry,
    generate_components,
    get_donation,
    list_blood_units,
    list_donations,
    record_donation,
)
from app.blood_bank.donor_service import defer_donor, register_donor
from app.blood_bank.screening_service import conduct_screening
from app.db import Base
from app.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
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


def _setup_donation_env(db: Session):
    t1 = Tenant(id=str(uuid.uuid4()), name="Alpha Blood Bank", code=f"ABB_{uuid.uuid4().hex[:6]}")
    t2 = Tenant(id=str(uuid.uuid4()), name="Beta Blood Bank", code=f"BBB_{uuid.uuid4().hex[:6]}")
    db.add_all([t1, t2])
    db.flush()

    b1 = Branch(id=str(uuid.uuid4()), tenant_id=t1.id, name="Alpha Main", code="AM")
    b2 = Branch(id=str(uuid.uuid4()), tenant_id=t2.id, name="Beta Main", code="BM")
    db.add_all([b1, b2])
    db.flush()

    perms = [
        Permission(code="blood.donor.create", module="blood_bank", resource="donor", action="create", risk_level="normal"),
        Permission(code="blood.donor.screen", module="blood_bank", resource="donor", action="screen", risk_level="high"),
        Permission(code="blood.unit.receive", module="blood_bank", resource="unit", action="receive", risk_level="normal"),
    ]
    db.add_all(perms)
    db.flush()

    role_officer = Role(tenant_id=t1.id, name="Phlebotomy Officer", is_system=False)
    role_ro = Role(tenant_id=t1.id, name="Read Only", is_system=False)
    role_t2 = Role(tenant_id=t2.id, name="T2 Officer", is_system=False)
    db.add_all([role_officer, role_ro, role_t2])
    db.flush()

    for p in perms:
        db.add(RolePermission(role_id=role_officer.id, permission_id=p.id, allow=True))
        db.add(RolePermission(role_id=role_t2.id, permission_id=p.id, allow=True))

    user_officer = User(tenant_id=t1.id, email="phleb@alpha.org", username="alpha_phleb", hashed_password="pw")
    user_ro = User(tenant_id=t1.id, email="ro@alpha.org", username="alpha_ro", hashed_password="pw")
    user_t2 = User(tenant_id=t2.id, email="phleb@beta.org", username="beta_phleb", hashed_password="pw")
    db.add_all([user_officer, user_ro, user_t2])
    db.flush()

    db.add_all([
        UserRole(user_id=user_officer.id, role_id=role_officer.id),
        UserRole(user_id=user_ro.id, role_id=role_ro.id),
        UserRole(user_id=user_t2.id, role_id=role_t2.id),
    ])

    ctx_officer = TenantContext(tenant_id=t1.id, branch_id=b1.id, user_id=user_officer.id)
    ctx_ro = TenantContext(tenant_id=t1.id, branch_id=b1.id, user_id=user_ro.id)
    ctx2 = TenantContext(tenant_id=t2.id, branch_id=b2.id, user_id=user_t2.id)

    db.commit()

    return {
        "ctx_officer": ctx_officer,
        "ctx_ro": ctx_ro,
        "ctx2": ctx2,
    }


def test_record_donation_single_bag(db_session: Session):
    env = _setup_donation_env(db_session)
    ctx = env["ctx_officer"]

    donor = register_donor(
        db_session,
        tenant_context=ctx,
        first_name="Arthur",
        last_name="Dent",
        sex="male",
        date_of_birth=date(1985, 4, 12),
        blood_group="O_POS",
    )

    donation = record_donation(
        db_session,
        tenant_context=ctx,
        donor_id=donor.id,
        bag_type="single",
        donation_type="whole_blood",
        volume_ml=450,
        venipuncture_site="right_antecubital",
        status="completed",
    )

    assert donation.donation_no.startswith("DON-")
    assert donation.status == "completed"
    assert donation.blood_group == "O_POS"
    assert len(donation.blood_units) == 1

    unit = donation.blood_units[0]
    assert unit.unit_no == f"{donation.donation_no}-WB"
    assert unit.component_type == "whole_blood"
    assert unit.blood_group == "O_POS"
    assert unit.status == "collected"
    assert unit.volume_ml == 450
    assert (unit.expiry_at - donation.donated_at).days == 35

    db_session.refresh(donor)
    assert donor.total_donations == 1
    donor_last = donor.last_donation_date.date() if isinstance(donor.last_donation_date, datetime) else donor.last_donation_date
    assert donor_last == donation.donated_at.date()



def test_record_donation_triple_and_quadruple_fractionation(db_session: Session):
    env = _setup_donation_env(db_session)
    ctx = env["ctx_officer"]

    donor1 = register_donor(
        db_session,
        tenant_context=ctx,
        first_name="Ford",
        last_name="Prefect",
        sex="male",
        date_of_birth=date(1980, 1, 1),
        blood_group="A_POS",
    )

    don_triple = record_donation(
        db_session,
        tenant_context=ctx,
        donor_id=donor1.id,
        bag_type="triple",
        volume_ml=450,
    )

    units_triple = don_triple.blood_units
    assert len(units_triple) == 3
    type_map = {u.component_type: u for u in units_triple}
    assert "packed_red_cells" in type_map
    assert "fresh_frozen_plasma" in type_map
    assert "platelet_concentrate" in type_map

    prbc = type_map["packed_red_cells"]
    ffp = type_map["fresh_frozen_plasma"]
    pc = type_map["platelet_concentrate"]

    assert (prbc.expiry_at - don_triple.donated_at).days == 42
    assert (ffp.expiry_at - don_triple.donated_at).days == 365
    assert (pc.expiry_at - don_triple.donated_at).days == 5

    donor2 = register_donor(
        db_session,
        tenant_context=ctx,
        first_name="Trillian",
        last_name="Astra",
        sex="female",
        date_of_birth=date(1990, 6, 15),
        blood_group="B_NEG",
    )

    don_quad = record_donation(
        db_session,
        tenant_context=ctx,
        donor_id=donor2.id,
        bag_type="quadruple",
        volume_ml=450,
    )

    assert len(don_quad.blood_units) == 4
    quad_types = {u.component_type for u in don_quad.blood_units}
    assert quad_types == {
        "packed_red_cells",
        "fresh_frozen_plasma",
        "platelet_concentrate",
        "cryoprecipitate",
    }


def test_donation_interval_rejection(db_session: Session):
    env = _setup_donation_env(db_session)
    ctx = env["ctx_officer"]

    donor = register_donor(
        db_session,
        tenant_context=ctx,
        first_name="Zaphod",
        last_name="Beeblebrox",
        sex="male",
        date_of_birth=date(1975, 5, 5),
    )

    record_donation(
        db_session,
        tenant_context=ctx,
        donor_id=donor.id,
        bag_type="single",
    )

    with pytest.raises(ConflictError) as exc:
        record_donation(
            db_session,
            tenant_context=ctx,
            donor_id=donor.id,
            bag_type="single",
        )
    assert "Minimum donation interval not met" in str(exc.value)



def test_donation_deferred_donor_rejection(db_session: Session):
    env = _setup_donation_env(db_session)
    ctx = env["ctx_officer"]

    donor = register_donor(
        db_session,
        tenant_context=ctx,
        first_name="Slartibartfast",
        last_name="Magrathea",
        sex="male",
        date_of_birth=date(1985, 2, 2),
    )

    defer_donor(
        db_session,
        tenant_context=ctx,
        donor_id=donor.id,
        deferral_type="temporary",
        reason="Recent antibiotics therapy",
        deferred_until=datetime.now(timezone.utc) + timedelta(days=14),
    )

    with pytest.raises(ConflictError) as exc:
        record_donation(
            db_session,
            tenant_context=ctx,
            donor_id=donor.id,
            bag_type="single",
        )
    assert "Donor is currently deferred" in str(exc.value)


def test_donation_screening_linkage(db_session: Session):
    env = _setup_donation_env(db_session)
    ctx = env["ctx_officer"]

    donor = register_donor(
        db_session,
        tenant_context=ctx,
        first_name="Tricia",
        last_name="McMillan",
        sex="female",
        date_of_birth=date(1991, 7, 7),
    )

    screening_passed = conduct_screening(
        db_session,
        tenant_context=ctx,
        donor_id=donor.id,
        weight_kg=62.0,
        hemoglobin_g_dl=13.5,
        blood_pressure_systolic=115,
        blood_pressure_diastolic=75,
        pulse_bpm=72,
        temperature_c=36.7,
    )
    assert screening_passed.status == "passed"

    donation = record_donation(
        db_session,
        tenant_context=ctx,
        donor_id=donor.id,
        screening_id=screening_passed.id,
        bag_type="double",
    )
    assert donation.screening_id == screening_passed.id
    assert donation.status == "completed"
    assert len(donation.blood_units) == 2


def test_manual_component_generation_and_inventory(db_session: Session):
    env = _setup_donation_env(db_session)
    ctx = env["ctx_officer"]

    donor = register_donor(
        db_session,
        tenant_context=ctx,
        first_name="Marvin",
        last_name="Paranoid",
        sex="male",
        date_of_birth=date(1982, 3, 3),
        blood_group="AB_POS",
    )

    donation = record_donation(
        db_session,
        tenant_context=ctx,
        donor_id=donor.id,
        bag_type="double",
        auto_generate_components=False,
    )
    assert len(donation.blood_units) == 0

    units = generate_components(db_session, tenant_context=ctx, donation_id=donation.id)
    assert len(units) == 2

    with pytest.raises(ConflictError):
        generate_components(db_session, tenant_context=ctx, donation_id=donation.id)

    inventory = list_blood_units(db_session, tenant_context=ctx, blood_group="AB_POS")
    assert len(inventory) == 2


def test_rbac_and_tenant_isolation(db_session: Session):
    env = _setup_donation_env(db_session)
    ctx = env["ctx_officer"]
    ctx_ro = env["ctx_ro"]
    ctx2 = env["ctx2"]

    donor = register_donor(
        db_session,
        tenant_context=ctx,
        first_name="Eddie",
        last_name="Computer",
        sex="male",
        date_of_birth=date(1988, 8, 8),
    )

    with pytest.raises(ForbiddenError):
        record_donation(
            db_session,
            tenant_context=ctx_ro,
            donor_id=donor.id,
            bag_type="single",
        )

    donation = record_donation(
        db_session,
        tenant_context=ctx,
        donor_id=donor.id,
        bag_type="single",
    )

    with pytest.raises(NotFoundError):
        get_donation(db_session, tenant_context=ctx2, donation_id=donation.id)

    assert len(list_donations(db_session, tenant_context=ctx2)) == 0
    assert len(list_blood_units(db_session, tenant_context=ctx2)) == 0


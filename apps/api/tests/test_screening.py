"""Tests for P07-02: Screening (Questionnaire, Clinical Vitals, Eligibility, Deferral Workflow)."""
import json
import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.audit.service import get_audit_logs
from app.blood_bank.donor_service import register_donor
from app.blood_bank.screening_service import (
    conduct_screening,
    get_screening,
    get_screening_questionnaire_template,
    list_screenings,
    list_screenings_for_donor,
)
from app.db import Base
from app.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.blood_bank import Donor, DonorDeferral, DonorScreening
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


def _setup_screening_env(db: Session):
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
    role_t2 = Role(tenant_id=t2.id, name="T2 Officer", is_system=False)
    db.add_all([role_officer, role_ro, role_t2])
    db.flush()

    for p in perms:
        db.add(RolePermission(role_id=role_officer.id, permission_id=p.id, allow=True))
        db.add(RolePermission(role_id=role_t2.id, permission_id=p.id, allow=True))

    user_officer = User(tenant_id=t1.id, email="officer@cbc.com", username="bb_officer", hashed_password="pw")
    user_ro = User(tenant_id=t1.id, email="ro@cbc.com", username="ro_user", hashed_password="pw")
    user_t2 = User(tenant_id=t2.id, email="officer@rbb.com", username="t2_officer", hashed_password="pw")
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


def test_questionnaire_template():
    questions = get_screening_questionnaire_template()
    keys = {q["key"] for q in questions}
    assert "feeling_well" in keys
    assert "tattoo_or_piercing_last_6_months" in keys
    assert "cardiac_renal_disease" in keys
    assert "high_risk_behavior" in keys
    assert len(questions) >= 7


def test_successful_screening_workflow(db_session: Session):
    env = _setup_screening_env(db_session)
    ctx = env["ctx_officer"]

    donor = register_donor(
        db_session,
        tenant_context=ctx,
        first_name="Marie",
        last_name="Curie",
        sex="female",
        date_of_birth=date(1985, 11, 7),
        blood_group="B+",
    )

    screening = conduct_screening(
        db_session,
        tenant_context=ctx,
        donor_id=donor.id,
        weight_kg=62.5,
        blood_pressure_systolic=120,
        blood_pressure_diastolic=80,
        pulse_bpm=72,
        temperature_c=36.7,
        hemoglobin_g_dl=13.8,
        questionnaire_responses={
            "feeling_well": True,
            "recent_fever_or_infection": False,
            "antibiotics_last_14_days": False,
            "major_surgery_last_6_months": False,
            "tattoo_or_piercing_last_6_months": False,
            "cardiac_renal_disease": False,
            "high_risk_behavior": False,
            "pregnant_or_lactating": False,
        },
    )

    assert screening.id is not None
    assert screening.screening_no.startswith("SCR-")
    assert screening.status == "passed"
    assert screening.eligibility_status == "eligible"
    assert screening.deferral_id is None
    assert screening.deferral_reason is None

    # Audit trail check
    logs = get_audit_logs(db_session, tenant_id=ctx.tenant_id, entity_type="donor_screening", entity_id=screening.id)
    assert any(l.action_code == "blood.screening.conducted" for l in logs)

    # Retrieval
    fetched = get_screening(db_session, tenant_context=ctx, screening_id=screening.id)
    assert fetched.screening_no == screening.screening_no
    assert fetched.donor.first_name == "Marie"


def test_vitals_failure_temporary_deferral(db_session: Session):
    env = _setup_screening_env(db_session)
    ctx = env["ctx_officer"]

    donor = register_donor(
        db_session,
        tenant_context=ctx,
        first_name="Ada",
        last_name="Lovelace",
        sex="female",
        date_of_birth=date(1992, 12, 10),
    )

    # Low hemoglobin (11.2 g/dL < 12.5) and borderline low weight (43.0 kg < 45.0)
    screening = conduct_screening(
        db_session,
        tenant_context=ctx,
        donor_id=donor.id,
        weight_kg=43.0,
        hemoglobin_g_dl=11.2,
        questionnaire_responses={"feeling_well": True},
    )

    assert screening.status == "deferred_temporary"
    assert screening.eligibility_status == "ineligible"
    assert "Hemoglobin" in screening.deferral_reason
    assert "Weight" in screening.deferral_reason
    assert screening.deferral_id is not None
    assert screening.deferred_until is not None

    # Check donor status updated
    db_session.refresh(donor)
    assert donor.status == "deferred_temporary"

    # Check created deferral
    deferral = db_session.query(DonorDeferral).filter(DonorDeferral.id == screening.deferral_id).first()
    assert deferral is not None
    assert deferral.deferral_type == "temporary"
    assert deferral.status == "active"



def test_questionnaire_permanent_deferral(db_session: Session):
    env = _setup_screening_env(db_session)
    ctx = env["ctx_officer"]

    donor = register_donor(
        db_session,
        tenant_context=ctx,
        first_name="Robert",
        last_name="Koch",
        sex="male",
        date_of_birth=date(1975, 5, 20),
    )

    screening = conduct_screening(
        db_session,
        tenant_context=ctx,
        donor_id=donor.id,
        weight_kg=78.0,
        hemoglobin_g_dl=15.0,
        questionnaire_responses={
            "feeling_well": True,
            "cardiac_renal_disease": True,  # Cardiac condition triggers permanent deferral
        },
    )

    assert screening.status == "deferred_permanent"
    assert screening.eligibility_status == "ineligible"
    assert screening.deferral_id is not None
    assert "cardiovascular" in screening.deferral_reason.lower()

    db_session.refresh(donor)
    assert donor.status == "deferred_permanent"

    # Subsequent screening attempt on permanently deferred donor is blocked
    with pytest.raises(ConflictError):
        conduct_screening(
            db_session,
            tenant_context=ctx,
            donor_id=donor.id,
            weight_kg=78.0,
            hemoglobin_g_dl=15.0,
        )


def test_rbac_and_tenant_isolation(db_session: Session):
    env = _setup_screening_env(db_session)
    ctx = env["ctx_officer"]
    ctx_ro = env["ctx_ro"]
    ctx2 = env["ctx2"]

    donor = register_donor(
        db_session,
        tenant_context=ctx,
        first_name="Wilhelm",
        last_name="Rontgen",
        sex="male",
        date_of_birth=date(1982, 3, 27),
    )

    # 1. RBAC: User without blood.donor.screen cannot conduct screening
    with pytest.raises(ForbiddenError):
        conduct_screening(
            db_session,
            tenant_context=ctx_ro,
            donor_id=donor.id,
            weight_kg=70.0,
            hemoglobin_g_dl=14.0,
        )

    # 2. Multi-tenant isolation: Tenant 2 cannot screen Tenant 1 donor
    with pytest.raises(NotFoundError):
        conduct_screening(
            db_session,
            tenant_context=ctx2,
            donor_id=donor.id,
            weight_kg=70.0,
            hemoglobin_g_dl=14.0,
        )

    # 3. List screenings scoped to tenant
    screening = conduct_screening(
        db_session,
        tenant_context=ctx,
        donor_id=donor.id,
        weight_kg=70.0,
        hemoglobin_g_dl=14.0,
        questionnaire_responses={"feeling_well": True},
    )

    items_t1, total_t1 = list_screenings(db_session, tenant_context=ctx)
    items_t2, total_t2 = list_screenings(db_session, tenant_context=ctx2)
    assert total_t1 == 1
    assert total_t2 == 0

    donor_screenings, count = list_screenings_for_donor(db_session, tenant_context=ctx, donor_id=donor.id)
    assert count == 1
    assert donor_screenings[0].screening_no == screening.screening_no


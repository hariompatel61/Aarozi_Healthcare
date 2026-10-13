"""Tests for P03-06: Profiles and Packages and item expansion."""
from __future__ import annotations

import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.errors import ConflictError, NotFoundError, ValidationError
from app.models.core import Tenant, Branch, Department
from app.models.identity import User
from app.models.pathology import Test
from app.pathology.test_master import create_test
from app.pathology.profiles_packages import (
    create_package,
    create_profile,
    expand_ordered_items,
    get_package,
    get_profile,
    list_packages,
    list_profiles,
)
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


def test_create_and_get_profile(db_session: Session):
    tenant = Tenant(id=str(uuid.uuid4()), name="Profile Lab", code="PLAB", is_active=True)
    user = User(id=str(uuid.uuid4()), tenant_id=tenant.id, username="admin1", email="a@l.org", hashed_password="pwd")
    db_session.add_all([tenant, user])
    db_session.flush()

    ctx = TenantContext(tenant_id=tenant.id)

    t1 = create_test(db_session, tenant_context=ctx, code="SGOT", name="SGOT / AST", unit="U/L")
    t2 = create_test(db_session, tenant_context=ctx, code="SGPT", name="SGPT / ALT", unit="U/L")
    t3 = create_test(db_session, tenant_context=ctx, code="ALP", name="Alkaline Phosphatase", unit="U/L")
    db_session.flush()

    profile = create_profile(
        db_session,
        tenant_context=ctx,
        code="LFT-CORE",
        name="Liver Function Tests Core",
        test_ids=[t1.id, t2.id, t3.id],
        actor_user_id=user.id,
    )
    db_session.commit()

    assert profile.id is not None
    assert profile.code == "LFT-CORE"
    assert len(profile.items) == 3

    fetched = get_profile(db_session, tenant_context=ctx, profile_id=profile.id)


def test_profile_unique_code_and_validation(db_session: Session):
    tenant = Tenant(id=str(uuid.uuid4()), name="Val Lab", code="VL", is_active=True)
    db_session.add(tenant)
    db_session.flush()
    ctx = TenantContext(tenant_id=tenant.id)

    with pytest.raises(ValidationError):
        create_profile(db_session, tenant_context=ctx, code="", name="Name")

    with pytest.raises(ValidationError):
        create_profile(db_session, tenant_context=ctx, code="PROF1", name=" ")

    p1 = create_profile(db_session, tenant_context=ctx, code="PROF1", name="Profile One")
    db_session.commit()

    with pytest.raises(ConflictError):
        create_profile(db_session, tenant_context=ctx, code="PROF1", name="Duplicate Prof")


def test_create_package_with_tests_and_profiles(db_session: Session):
    tenant = Tenant(id=str(uuid.uuid4()), name="Pkg Lab", code="PKG", is_active=True)
    db_session.add(tenant)
    db_session.flush()
    ctx = TenantContext(tenant_id=tenant.id)

    t_glu = create_test(db_session, tenant_context=ctx, code="GLU", name="Glucose Fasting")
    t_chol = create_test(db_session, tenant_context=ctx, code="CHOL", name="Total Cholesterol")
    t_trig = create_test(db_session, tenant_context=ctx, code="TRIG", name="Triglycerides")
    db_session.flush()

    lipid_prof = create_profile(
        db_session,
        tenant_context=ctx,
        code="LIPID",
        name="Lipid Profile",
        test_ids=[t_chol.id, t_trig.id],
    )
    db_session.flush()

    pkg = create_package(
        db_session,
        tenant_context=ctx,
        code="HEALTH-CHECK-BASIC",
        name="Basic Health Checkup",
        items=[
            {"test_id": t_glu.id},
            {"profile_id": lipid_prof.id},
        ],
    )
    db_session.commit()

    assert pkg.id is not None
    assert pkg.code == "HEALTH-CHECK-BASIC"
    assert len(pkg.items) == 2

    fetched_pkg = get_package(db_session, tenant_context=ctx, package_id=pkg.id)
    assert len(fetched_pkg.items) == 2


def test_expand_ordered_items_hierarchy_and_deduplication(db_session: Session):
    tenant = Tenant(id=str(uuid.uuid4()), name="Expand Lab", code="EL", is_active=True)
    db_session.add(tenant)
    db_session.flush()
    ctx = TenantContext(tenant_id=tenant.id)

    t_hb = create_test(db_session, tenant_context=ctx, code="HB", name="Hemoglobin")
    t_wbc = create_test(db_session, tenant_context=ctx, code="WBC", name="White Blood Cells")
    t_plt = create_test(db_session, tenant_context=ctx, code="PLT", name="Platelet Count")
    t_glu = create_test(db_session, tenant_context=ctx, code="GLU", name="Fasting Glucose")
    db_session.flush()

    cbc_profile = create_profile(
        db_session,
        tenant_context=ctx,
        code="CBC",
        name="Complete Blood Count",
        test_ids=[t_hb.id, t_wbc.id, t_plt.id],
    )
    db_session.flush()

    wellness_package = create_package(
        db_session,
        tenant_context=ctx,
        code="WELL-1",
        name="Wellness 1",
        items=[
            {"profile_id": cbc_profile.id},
            {"test_id": t_glu.id},
        ],
    )
    db_session.commit()

    expanded = expand_ordered_items(
        db_session,
        tenant_context=ctx,
        items=[{"type": "package", "id": wellness_package.id}],
    )
    assert len(expanded) == 4
    test_codes = {item["code"] for item in expanded}
    assert test_codes == {"HB", "WBC", "PLT", "GLU"}

    expanded_multi = expand_ordered_items(
        db_session,
        tenant_context=ctx,
        items=[
            {"type": "package", "id": wellness_package.id},
            {"type": "test", "id": t_hb.id},
            {"type": "profile", "id": cbc_profile.id},
        ],
    )
    assert len(expanded_multi) == 4
    hb_item = next(i for i in expanded_multi if i["code"] == "HB")
    assert len(hb_item["sources"]) == 3


def test_tenant_isolation_in_profiles_and_packages(db_session: Session):
    t1 = Tenant(id=str(uuid.uuid4()), name="Tenant 1", code="T1", is_active=True)
    t2 = Tenant(id=str(uuid.uuid4()), name="Tenant 2", code="T2", is_active=True)
    db_session.add_all([t1, t2])
    db_session.flush()

    ctx1 = TenantContext(tenant_id=t1.id)
    ctx2 = TenantContext(tenant_id=t2.id)

    t1_test = create_test(db_session, tenant_context=ctx1, code="T1_TEST", name="T1 Test")
    t2_test = create_test(db_session, tenant_context=ctx2, code="T2_TEST", name="T2 Test")
    db_session.flush()

    p1 = create_profile(db_session, tenant_context=ctx1, code="PROF1", name="Profile T1", test_ids=[t1_test.id])
    db_session.commit()

    with pytest.raises(NotFoundError):
        get_profile(db_session, tenant_context=ctx2, profile_id=p1.id)

    p_list_2 = list_profiles(db_session, tenant_context=ctx2)
    assert len(p_list_2) == 0

    p_list_1 = list_profiles(db_session, tenant_context=ctx1)
    assert len(p_list_1) == 1
    assert p_list_1[0].code == "PROF1"

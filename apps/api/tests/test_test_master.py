"""Tests for P03-05 Test Master: tests, specimens, methods, units, reference ranges, and active versioning."""
from __future__ import annotations

import uuid
from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.errors import ConflictError, NotFoundError, ValidationError
from app.models.core import Tenant, Branch, Department
from app.models.identity import User
from app.models.pathology import Test, TestReferenceRange
from app.pathology.test_master import (
    create_new_test_version,
    create_test,
    get_active_test_by_code,
    get_test,
    list_tests,
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


def test_create_test_with_specimen_method_units_and_ranges(db_session: Session):
    tenant = Tenant(id=str(uuid.uuid4()), name="Alpha Lab", code="ALPHA", is_active=True)
    branch = Branch(id=str(uuid.uuid4()), tenant_id=tenant.id, name="Main Branch", code="MB01", is_active=True)
    dept = Department(id=str(uuid.uuid4()), tenant_id=tenant.id, branch_id=branch.id, name="Biochemistry", code="BIO")
    user = User(id=str(uuid.uuid4()), tenant_id=tenant.id, username="pathologist1", email="path@lab.org", hashed_password="hash")
    db_session.add_all([tenant, branch, dept, user])
    db_session.flush()

    ctx = TenantContext(tenant_id=tenant.id)

    ranges = [
        {
            "sex": "all",
            "age_min": 0,
            "age_max": 120,
            "low_value": Decimal("70.0"),
            "high_value": Decimal("99.0"),
            "critical_low": Decimal("40.0"),
            "critical_high": Decimal("400.0"),
            "text_range": "70 - 99 mg/dL",
        }
    ]

    test = create_test(
        db_session,
        tenant_context=ctx,
        department_id=dept.id,
        code="GLU-F",
        name="Fasting Blood Glucose",
        display_name="Glucose, Fasting",
        short_name="FBG",
        specimen_type="Fluoride Plasma",
        container_type="Grey Top Tube (Sodium Fluoride)",
        method="Hexokinase",
        unit="mg/dL",
        decimal_precision=1,
        analyzer_code="COBAS-GLU",
        loinc_code="1558-6",
        reference_ranges=ranges,
        actor_user_id=user.id,
    )
    db_session.commit()

    assert test.id is not None
    assert test.code == "GLU-F"
    assert test.version == 1
    assert test.status == "active"
    assert test.specimen_type == "Fluoride Plasma"
    assert test.container_type == "Grey Top Tube (Sodium Fluoride)"
    assert test.method == "Hexokinase"
    assert test.unit == "mg/dL"
def test_active_versioning_and_superseded_flow(db_session: Session):
    tenant = Tenant(id=str(uuid.uuid4()), name="Metropolis Health", code="METRO", is_active=True)
    db_session.add(tenant)
    db_session.flush()

    ctx = TenantContext(tenant_id=tenant.id)

    v1 = create_test(
        db_session,
        tenant_context=ctx,
        code="CREAT",
        name="Creatinine, Serum",
        specimen_type="Serum",
        container_type="Red Top / SST",
        method="Jaffe alkaline picrate",
        unit="mg/dL",
        decimal_precision=2,
        reference_ranges=[
            {"sex": "male", "age_min": 18, "age_max": 100, "low_value": Decimal("0.70"), "high_value": Decimal("1.30")},
            {"sex": "female", "age_min": 18, "age_max": 100, "low_value": Decimal("0.50"), "high_value": Decimal("1.10")},
        ],
    )
    db_session.commit()

    assert v1.version == 1
    assert v1.status == "active"

    active = get_active_test_by_code(db_session, tenant_context=ctx, code="CREAT")
    assert active.id == v1.id
    assert active.version == 1

    v2 = create_new_test_version(
        db_session,
        tenant_context=ctx,
        test_id=v1.id,
        update_data={
            "method": "Enzymatic UV",
            "decimal_precision": 2,
            "reference_ranges": [
                {"sex": "male", "age_min": 18, "age_max": 100, "low_value": Decimal("0.67"), "high_value": Decimal("1.17")},
                {"sex": "female", "age_min": 18, "age_max": 100, "low_value": Decimal("0.51"), "high_value": Decimal("0.95")},
            ],
        },
        reason="Switched analyzer methodology from Jaffe to Enzymatic UV",
    )
    db_session.commit()

    db_session.refresh(v1)
    db_session.refresh(v2)

    assert v1.status == "superseded"
    assert v1.effective_to is not None
    assert v2.version == 2
    assert v2.status == "active"
    assert v2.method == "Enzymatic UV"
    assert v2.specimen_type == "Serum"

    active_now = get_active_test_by_code(db_session, tenant_context=ctx, code="CREAT")
    assert active_now.id == v2.id
    assert active_now.version == 2
    assert active_now.method == "Enzymatic UV"


def test_tenant_isolation_in_test_master(db_session: Session):
    t1 = Tenant(id=str(uuid.uuid4()), name="Lab 1", code="L1", is_active=True)
    t2 = Tenant(id=str(uuid.uuid4()), name="Lab 2", code="L2", is_active=True)
    db_session.add_all([t1, t2])
    db_session.flush()

    ctx1 = TenantContext(tenant_id=t1.id)
    ctx2 = TenantContext(tenant_id=t2.id)

    test_t1 = create_test(db_session, tenant_context=ctx1, code="CBC", name="Complete Blood Count", unit="Various")
    test_t2 = create_test(db_session, tenant_context=ctx2, code="CBC", name="Complete Blood Count Lab2", unit="Various")
    db_session.commit()

    assert test_t1.id != test_t2.id

    found1 = get_active_test_by_code(db_session, tenant_context=ctx1, code="CBC")
    assert found1.id == test_t1.id
    assert found1.tenant_id == t1.id

    with pytest.raises(NotFoundError):
        get_test(db_session, tenant_context=ctx1, test_id=test_t2.id)


def test_test_master_validations(db_session: Session):
    tenant = Tenant(id=str(uuid.uuid4()), name="Lab Val", code="LV", is_active=True)
    db_session.add(tenant)
    db_session.flush()

    ctx = TenantContext(tenant_id=tenant.id)

    with pytest.raises(ValidationError):
        create_test(db_session, tenant_context=ctx, code="", name="Test Name")

    with pytest.raises(ValidationError):
        create_test(db_session, tenant_context=ctx, code="T1", name="  ")

    create_test(db_session, tenant_context=ctx, code="HB", name="Hemoglobin")
    db_session.commit()

    with pytest.raises(ConflictError):
        create_test(db_session, tenant_context=ctx, code="HB", name="Hemoglobin Duplicate")


def test_list_tests_bounded_and_filtered(db_session: Session):
    tenant = Tenant(id=str(uuid.uuid4()), name="Search Lab", code="SL", is_active=True)
    db_session.add(tenant)
    db_session.flush()

    ctx = TenantContext(tenant_id=tenant.id)

    create_test(db_session, tenant_context=ctx, code="ALT", name="Alanine Aminotransferase", specimen_type="Serum")
    create_test(db_session, tenant_context=ctx, code="AST", name="Aspartate Aminotransferase", specimen_type="Serum")
    create_test(db_session, tenant_context=ctx, code="CBC", name="Complete Blood Count", specimen_type="EDTA Whole Blood")
    db_session.commit()

    all_tests = list_tests(db_session, tenant_context=ctx)
    assert len(all_tests) == 3

    serum_tests = list_tests(db_session, tenant_context=ctx, specimen_type="Serum")
    assert len(serum_tests) == 2
    assert {t.code for t in serum_tests} == {"ALT", "AST"}

    search_results = list_tests(db_session, tenant_context=ctx, search="amino")
    assert len(search_results) == 2

    bounded = list_tests(db_session, tenant_context=ctx, limit=100)
    assert len(bounded) <= 50


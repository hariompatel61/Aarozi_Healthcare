"""Tests for P03-02 Patient Search.

Verifies global patient search with mobile, UHID, barcode inputs,
fuzzy name lookup, bounding and strict multi-tenant safety.
"""
from datetime import date
import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.models.core import Tenant, Branch
from app.models.patient import Patient, PatientIdentifier
from app.security.tenant_guard import TenantContext
from app.patient.search import (
    search_patients,
    get_patient_by_uhid,
    get_patient_by_identifier,
    normalize_mobile,
)


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


@pytest.fixture
def test_data(db_session: Session):
    t1 = Tenant(id=str(uuid.uuid4()), name="Hospital One", code="H1", is_active=True)
    t2 = Tenant(id=str(uuid.uuid4()), name="Hospital Two", code="H2", is_active=True)
    b1 = Branch(id=str(uuid.uuid4()), tenant_id=t1.id, name="B1", code="B1", is_active=True)
    db_session.add_all([t1, t2, b1])
    db_session.commit()

    # Patient 1 (in T1)
    p1 = Patient(
        tenant_id=t1.id,
        branch_id=b1.id,
        patient_no="UHID-10001",
        first_name="Fatima",
        last_name="Zahra",
        mobile_normalized="+923001234567",
        sex="female",
    )
    # Patient 2 (in T1)
    p2 = Patient(
        tenant_id=t1.id,
        branch_id=b1.id,
        patient_no="UHID-10002",
        first_name="Zahid",
        last_name="Khan",
        mobile_normalized="+923219876543",
        sex="male",
    )
    # Patient 3 in T2 with SAME mobile to test tenant isolation
    p3 = Patient(
        tenant_id=t2.id,
        patient_no="UHID-20001",
        first_name="CrossTenant",
        last_name="Person",
        mobile_normalized="+923001234567",
        sex="male",
    )
    db_session.add_all([p1, p2, p3])
    db_session.commit()

    # Barcode & MRN identifiers
    id1 = PatientIdentifier(
        tenant_id=t1.id,
        patient_id=p1.id,
        identifier_type="BARCODE",
        identifier_value="BC-998877",
        is_primary=True,
    )
    id2 = PatientIdentifier(
        tenant_id=t1.id,
        patient_id=p2.id,
        identifier_type="MRN",
        identifier_value="MRN-4455",
        is_primary=True,
    )
    db_session.add_all([id1, id2])
    db_session.commit()

    return {
        "t1": t1,
        "t2": t2,
        "p1": p1,
        "p2": p2,
        "p3": p3,
    }


def test_normalize_mobile():
    assert normalize_mobile("+92 300-123 4567") == "+923001234567"
    assert normalize_mobile("(0300) 1234567") == "03001234567"
    assert normalize_mobile("") == ""
    assert normalize_mobile(None) == ""


def test_search_by_uhid(db_session: Session, test_data: dict):
    ctx1 = TenantContext(tenant_id=test_data["t1"].id)
    results = search_patients(db_session, ctx1, "UHID-10001")
    assert len(results) == 1
    assert results[0].patient_no == "UHID-10001"
    assert results[0].first_name == "Fatima"


def test_search_by_mobile_with_tenant_isolation(db_session: Session, test_data: dict):
    ctx1 = TenantContext(tenant_id=test_data["t1"].id)
    ctx2 = TenantContext(tenant_id=test_data["t2"].id)

    # Search in Tenant 1 returns only Fatima
    res1 = search_patients(db_session, ctx1, "03001234567")
    assert len(res1) == 1
    assert res1[0].id == test_data["p1"].id

    # Search same mobile in Tenant 2 returns only CrossTenant Person
    res2 = search_patients(db_session, ctx2, "03001234567")
    assert len(res2) == 1
    assert res2[0].id == test_data["p3"].id


def test_search_by_barcode(db_session: Session, test_data: dict):
    ctx1 = TenantContext(tenant_id=test_data["t1"].id)
    results = search_patients(db_session, ctx1, "BC-998877")
    assert len(results) == 1
    assert results[0].patient_no == "UHID-10001"


def test_search_by_name(db_session: Session, test_data: dict):
    ctx1 = TenantContext(tenant_id=test_data["t1"].id)
    # Search by first name
    res1 = search_patients(db_session, ctx1, "Fatima")
    assert len(res1) == 1
    assert res1[0].last_name == "Zahra"

    # Search by last name prefix
    res2 = search_patients(db_session, ctx1, "Kha")
    assert len(res2) == 1
    assert res2[0].first_name == "Zahid"


def test_get_patient_by_uhid(db_session: Session, test_data: dict):
    ctx1 = TenantContext(tenant_id=test_data["t1"].id)
    ctx2 = TenantContext(tenant_id=test_data["t2"].id)

    p = get_patient_by_uhid(db_session, ctx1, "UHID-10001")
    assert p is not None
    assert p.first_name == "Fatima"

    # Cross-tenant returns None
    p_cross = get_patient_by_uhid(db_session, ctx2, "UHID-10001")
    assert p_cross is None


def test_get_patient_by_identifier(db_session: Session, test_data: dict):
    ctx1 = TenantContext(tenant_id=test_data["t1"].id)
    p = get_patient_by_identifier(db_session, ctx1, "BARCODE", "BC-998877")
    assert p is not None
    assert p.patient_no == "UHID-10001"

    # Non-existent
    assert get_patient_by_identifier(db_session, ctx1, "BARCODE", "BC-NONE") is None

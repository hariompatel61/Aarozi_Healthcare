"""Tests for Patient and PatientIdentifier schema."""
from datetime import date
import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.models.core import Tenant, Branch
from app.models.patient import Patient, PatientIdentifier


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


def test_create_patient_and_identifiers(db_session: Session):
    tenant = Tenant(id=str(uuid.uuid4()), name="Test Hospital", code="TH01", is_active=True)
    branch = Branch(id=str(uuid.uuid4()), tenant_id=tenant.id, name="Main", code="BR01", is_active=True)
    db_session.add_all([tenant, branch])
    db_session.commit()

    patient = Patient(
        tenant_id=tenant.id,
        branch_id=branch.id,
        patient_no="P-10001",
        first_name="Ahmed",
        last_name="Ali",
        date_of_birth=date(1990, 5, 14),
        sex="male",
        mobile_normalized="+923001234567",
        blood_group="O+",
        address_json={"city": "Lahore", "country": "PK"},
        emergency_contact_json={"name": "Hassan", "phone": "+923007654321"},
    )
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)

    assert patient.id is not None
    assert patient.status == "active"
    assert patient.patient_no == "P-10001"

    # Add Identifiers
    cnic = PatientIdentifier(
        tenant_id=tenant.id,
        patient_id=patient.id,
        identifier_type="CNIC",
        identifier_value="35201-1234567-1",
        is_primary=True,
    )
    passport = PatientIdentifier(
        tenant_id=tenant.id,
        patient_id=patient.id,
        identifier_type="PASSPORT",
        identifier_value="AB123456",
        is_primary=False,
    )
    db_session.add_all([cnic, passport])
    db_session.commit()

    db_session.refresh(patient)
    assert len(patient.identifiers) == 2
    assert {i.identifier_type for i in patient.identifiers} == {"CNIC", "PASSPORT"}


def test_unique_patient_no_per_tenant(db_session: Session):
    tenant1 = Tenant(id=str(uuid.uuid4()), name="T1", code="T1", is_active=True)
    tenant2 = Tenant(id=str(uuid.uuid4()), name="T2", code="T2", is_active=True)
    db_session.add_all([tenant1, tenant2])
    db_session.commit()

    # Same patient_no in same tenant -> integrity error
    p1 = Patient(tenant_id=tenant1.id, patient_no="UHID-001", first_name="A")
    db_session.add(p1)
    db_session.commit()

    p2 = Patient(tenant_id=tenant1.id, patient_no="UHID-001", first_name="B")
    db_session.add(p2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Same patient_no in different tenant -> allowed
    p3 = Patient(tenant_id=tenant2.id, patient_no="UHID-001", first_name="C")
    db_session.add(p3)
    db_session.commit()
    assert p3.id is not None


def test_unique_patient_identifier_per_tenant(db_session: Session):
    tenant = Tenant(id=str(uuid.uuid4()), name="T1", code="T1", is_active=True)
    db_session.add(tenant)
    db_session.commit()

    p1 = Patient(tenant_id=tenant.id, patient_no="UHID-001", first_name="A")
    p2 = Patient(tenant_id=tenant.id, patient_no="UHID-002", first_name="B")
    db_session.add_all([p1, p2])
    db_session.commit()

    id1 = PatientIdentifier(
        tenant_id=tenant.id,
        patient_id=p1.id,
        identifier_type="CNIC",
        identifier_value="12345",
    )
    db_session.add(id1)
    db_session.commit()

    id2 = PatientIdentifier(
        tenant_id=tenant.id,
        patient_id=p2.id,
        identifier_type="CNIC",
        identifier_value="12345",
    )
    db_session.add(id2)
    with pytest.raises(IntegrityError):
        db_session.commit()

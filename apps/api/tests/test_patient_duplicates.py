"""Tests for P03-04 Duplicate Detection and Controlled Merge flow."""
from __future__ import annotations

import uuid
from datetime import date
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.errors import ConflictError, NotFoundError, ValidationError
from app.models.core import Tenant
from app.models.identity import User
from app.models.patient import Patient, PatientIdentifier, PatientMergeAudit
from app.patient.duplicates import (
    calculate_name_similarity,
    detect_duplicates,
    execute_patient_merge,
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


def test_name_similarity():
    assert calculate_name_similarity("Fatima", "Fatima") == 1.0
    assert calculate_name_similarity("Fatima", "Fatma") > 0.8
    assert calculate_name_similarity("John", "Doe") < 0.3
    assert calculate_name_similarity("", "Doe") == 0.0


def test_detect_duplicates_by_phone_and_identifier(db_session: Session):
    t1 = Tenant(id=str(uuid.uuid4()), name="Hospital One", code="H1", is_active=True)
    db_session.add(t1)
    db_session.flush()

    p1 = Patient(
        id=str(uuid.uuid4()),
        tenant_id=t1.id,
        patient_no="UHID-001",
        first_name="Zahid",
        last_name="Khan",
        mobile_normalized="+923001234567",
    )
    p2 = Patient(
        id=str(uuid.uuid4()),
        tenant_id=t1.id,
        patient_no="UHID-002",
        first_name="Zahid",
        last_name="Ahmed",
        mobile_normalized="+923210000000",
    )
    db_session.add_all([p1, p2])
    db_session.flush()

    id1 = PatientIdentifier(
        tenant_id=t1.id,
        patient_id=p1.id,
        identifier_type="CNIC",
        identifier_value="42101-1111111-1",
    )
    db_session.add(id1)
    db_session.flush()

    ctx = TenantContext(tenant_id=t1.id)

    # 1. Search by exact identifier
    matches = detect_duplicates(
        db_session,
        tenant_context=ctx,
        identifier_type="CNIC",
        identifier_value="42101-1111111-1",
    )
    assert len(matches) == 1
    assert matches[0].patient.id == p1.id
    assert matches[0].match_score == 1.0

    # 2. Search by phone
    matches_phone = detect_duplicates(
        db_session,
        tenant_context=ctx,
        mobile="0300 1234567",
    )
    assert len(matches_phone) == 1
    assert matches_phone[0].patient.id == p1.id
    assert matches_phone[0].match_score >= 0.85


def test_duplicate_detection_tenant_isolation(db_session: Session):
    t1 = Tenant(id=str(uuid.uuid4()), name="Hospital One", code="H1", is_active=True)
    t2 = Tenant(id=str(uuid.uuid4()), name="Hospital Two", code="H2", is_active=True)
    db_session.add_all([t1, t2])
    db_session.flush()

    p_t1 = Patient(
        id=str(uuid.uuid4()),
        tenant_id=t1.id,
        patient_no="UHID-001",
        first_name="Amina",
        last_name="Bibi",
        mobile_normalized="+923009999999",
    )
    p_t2 = Patient(
        id=str(uuid.uuid4()),
        tenant_id=t2.id,
        patient_no="UHID-002",
        first_name="Amina",
        last_name="Bibi",
        mobile_normalized="+923009999999",
    )
    db_session.add_all([p_t1, p_t2])
    db_session.flush()

    # Search in t1 context should NEVER see t2 patient
    ctx1 = TenantContext(tenant_id=t1.id)
    matches1 = detect_duplicates(db_session, tenant_context=ctx1, mobile="+923009999999")
    assert len(matches1) == 1
    assert matches1[0].patient.tenant_id == t1.id


def test_controlled_merge_flow_and_audit(db_session: Session):
    tenant = Tenant(id=str(uuid.uuid4()), name="Hospital Alpha", code="HA", is_active=True)
    actor = User(id=str(uuid.uuid4()), tenant_id=tenant.id, email="admin@hospital.com", username="admin", hashed_password="dummy")
    db_session.add_all([tenant, actor])
    db_session.flush()

    source = Patient(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        patient_no="UHID-OLD",
        first_name="Fatima",
        last_name="Zahra",
        blood_group="B+",
        mobile_normalized="+923001111111",
        status="active",
    )
    target = Patient(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        patient_no="UHID-NEW",
        first_name="Fatima",
        last_name="Zahra",
        blood_group=None,
        mobile_normalized=None,
        status="active",
    )
    db_session.add_all([source, target])
    db_session.flush()

    # Add identifiers to source
    src_ident = PatientIdentifier(
        tenant_id=tenant.id,
        patient_id=source.id,
        identifier_type="MRN",
        identifier_value="MRN-8877",
    )
    db_session.add(src_ident)
    db_session.flush()

    ctx = TenantContext(tenant_id=tenant.id)

    # Execute merge
    merge_audit = execute_patient_merge(
        db_session,
        tenant_context=ctx,
        source_patient_id=source.id,
        target_patient_id=target.id,
        reason="Duplicate registration consolidated by reception supervisor",
        actor_user_id=actor.id,
    )

    db_session.refresh(source)
    db_session.refresh(target)

    # 1. Source state verification
    assert source.status == "merged"
    assert source.merged_into_patient_id == target.id

    # 2. Target backfill verification
    assert target.blood_group == "B+"
    assert target.mobile_normalized == "+923001111111"

    # 3. Identifier transfer
    db_session.refresh(src_ident)
    assert src_ident.patient_id == target.id

    # 4. Audit trail
    assert merge_audit.source_patient_id == source.id
    assert merge_audit.target_patient_id == target.id
    assert merge_audit.actor_user_id == actor.id
    assert "reception supervisor" in merge_audit.reason

    # 5. Prevent double merge
    with pytest.raises(ConflictError):
        execute_patient_merge(
            db_session,
            tenant_context=ctx,
            source_patient_id=source.id,
            target_patient_id=target.id,
            reason="Attempt duplicate merge",
        )


def test_merge_validation_guards(db_session: Session):
    tenant = Tenant(id=str(uuid.uuid4()), name="Hospital Guard", code="HG", is_active=True)
    db_session.add(tenant)
    db_session.flush()

    p1 = Patient(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        patient_no="UHID-100",
        first_name="Ali",
        status="active",
    )
    db_session.add(p1)
    db_session.flush()

    ctx = TenantContext(tenant_id=tenant.id)

    # 1. Same source and target
    with pytest.raises(ValidationError):
        execute_patient_merge(
            db_session,
            tenant_context=ctx,
            source_patient_id=p1.id,
            target_patient_id=p1.id,
            reason="Same patient",
        )

    # 2. Empty reason
    with pytest.raises(ValidationError):
        execute_patient_merge(
            db_session,
            tenant_context=ctx,
            source_patient_id=p1.id,
            target_patient_id=str(uuid.uuid4()),
            reason="   ",
        )

    # 3. Missing patient
    with pytest.raises(NotFoundError):
        execute_patient_merge(
            db_session,
            tenant_context=ctx,
            source_patient_id=p1.id,
            target_patient_id=str(uuid.uuid4()),
            reason="Valid reason",
        )


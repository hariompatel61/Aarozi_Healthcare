"""Automated tests for patient data migration, duplicate detection, and rollback safety."""

import csv
import json
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base
from app.models.core import Tenant
from app.models.patient import Patient, PatientIdentifier
from app.services.migration_service import (
    auto_map_headers,
    parse_csv_content,
    detect_patient_duplicates,
    execute_patient_migration,
    export_complete_migration_package,
)


@pytest.fixture
def migration_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        tenant = Tenant(id="tenant_mig_01", name="City Pathology", code="CP01")
        session.add(tenant)
        session.commit()
        yield session


def test_auto_map_headers_legacy_synonyms():
    legacy_headers = ["Patient Name", "Contact_No", "Gender", "Patient_Age", "MRN", "Email Address"]
    mapped = auto_map_headers(legacy_headers)

    assert mapped["Patient Name"] == "first_name"
    assert mapped["Contact_No"] == "mobile"
    assert mapped["Gender"] == "sex"
    assert mapped["Patient_Age"] == "age"
    assert mapped["MRN"] == "legacy_id"
    assert mapped["Email Address"] == "email"


def test_parse_csv_content():
    raw_csv = """Patient Name,Mobile,Legacy MRN
Dr. Ramesh Sharma,9820012345,LEG-001
Sunita K. Deshmukh,9820054321,LEG-002
"""
    records = parse_csv_content(raw_csv)
    assert len(records) == 2
    assert records[0]["Patient Name"] == "Dr. Ramesh Sharma"
    assert records[0]["Mobile"] == "9820012345"


def test_duplicate_detection_by_mobile_and_mrn(migration_db):
    tenant_id = "tenant_mig_01"

    # Pre-populate one existing patient
    existing_p = Patient(
        id="p_existing_01",
        tenant_id=tenant_id,
        patient_no="P-EXIST-01",
        first_name="Ramesh",
        last_name="Sharma",
        mobile_normalized="9820012345",
        status="active",
        address_json={},
        emergency_contact_json={},
    )
    existing_id = PatientIdentifier(
        id="id_01",
        tenant_id=tenant_id,
        patient_id="p_existing_01",
        identifier_type="MIGRATED_SOURCE_ID",
        identifier_value="LEG-001",
    )
    migration_db.add_all([existing_p, existing_id])
    migration_db.commit()

    # Candidate records for migration
    candidates = [
        {"first_name": "Ramesh", "mobile": "9820012345", "legacy_id": "LEG-001"},  # Exact Duplicate
        {"first_name": "Anita", "mobile": "9999900000", "legacy_id": "LEG-002"},   # Brand New
    ]

    analysis = detect_patient_duplicates(migration_db, tenant_id, candidates)
    assert analysis[0]["is_duplicate"] is True
    assert "already exists" in analysis[0]["duplicate_reason"]
    assert analysis[1]["is_duplicate"] is False


def test_transactional_migration_with_skip_duplicate(migration_db):
    tenant_id = "tenant_mig_01"

    raw_data = [
        {"Name": "Patient One", "Phone": "9111111111", "MRN": "MRN-1"},
        {"Name": "Patient Two", "Phone": "9222222222", "MRN": "MRN-2"},
    ]
    mapping = {"Name": "first_name", "Phone": "mobile", "MRN": "legacy_id"}

    summary = execute_patient_migration(
        db=migration_db,
        tenant_id=tenant_id,
        raw_records=raw_data,
        field_mapping=mapping,
        conflict_strategy="SKIP_EXISTING",
        source_name="OLD_SYS_TEST",
    )

    assert summary["status"] == "success"
    assert summary["imported_count"] == 2
    assert summary["skipped_count"] == 0

    # Running exact same migration again with SKIP_EXISTING should skip all 2 duplicates
    summary2 = execute_patient_migration(
        db=migration_db,
        tenant_id=tenant_id,
        raw_records=raw_data,
        field_mapping=mapping,
        conflict_strategy="SKIP_EXISTING",
        source_name="OLD_SYS_TEST",
    )
    assert summary2["imported_count"] == 0
    assert summary2["skipped_count"] == 2


def test_export_complete_migration_package(migration_db):
    tenant_id = "tenant_mig_01"
    zip_bytes = export_complete_migration_package(migration_db, tenant_id)

    assert len(zip_bytes) > 0
    assert zip_bytes.startswith(b"PK")  # Standard ZIP magic bytes


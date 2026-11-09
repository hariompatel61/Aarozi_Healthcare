"""Integration test ensuring clinical database persistence and timestamp queries.
Verifies removal of hardcoded dummy data and presence of sample collection & report generation times.
"""

import pytest
from app.db import get_sync_session_factory
from app.models.core import Tenant
from app.models.patient import Patient
from app.models.pathology import Sample, Test, Order
from app.models.reporting import Report
from app.routers.pathology import get_dashboard_summary, list_samples
from app.routers.patients import list_or_search_patients


def test_database_has_seeded_patients_and_tests():
    """Verify patients, tests, and samples are stored relationally in the database."""
    factory = get_sync_session_factory()
    with factory() as db:
        tenant = db.query(Tenant).filter(Tenant.code == "AAROZI_HQ").first()
        assert tenant is not None, "AAROZI_HQ tenant must exist in database"

        patients = db.query(Patient).filter(Patient.tenant_id == tenant.id).all()
        assert len(patients) >= 6, "At least 6 clinical patients must be persisted in database"

        from sqlalchemy import or_
        tests = db.query(Test).filter(or_(Test.tenant_id == tenant.id, Test.is_system_default == True)).all()
        assert len(tests) >= 5, "Clinical test catalog must be populated in database"


def test_sample_collection_and_report_generation_times_persisted():
    """Verify sample collection time (collected_at) and report generation time (released_at) exist."""
    factory = get_sync_session_factory()
    with factory() as db:
        samples_with_collection_time = (
            db.query(Sample)
            .filter(Sample.collected_at.isnot(None))
            .all()
        )
        assert len(samples_with_collection_time) > 0, "Samples must have valid collected_at timestamps"

        sample = samples_with_collection_time[0]
        assert sample.collected_at is not None
        assert hasattr(sample.collected_at, "strftime")

        reports_with_generation_time = (
            db.query(Report)
            .filter(Report.released_at.isnot(None))
            .all()
        )
        assert len(reports_with_generation_time) > 0, "Reports must have valid released_at timestamps"

        report = reports_with_generation_time[0]
        assert report.released_at is not None
        assert hasattr(report.released_at, "strftime")


def test_dashboard_summary_returns_timestamps():
    """Verify dashboard endpoint exposes sample_collection_time and report_generation_time."""
    factory = get_sync_session_factory()
    with factory() as db:
        summary = get_dashboard_summary(db=db, tenant_context=None, current_user=None)
        assert "kpi_cards" in summary
        assert "recent_patients" in summary
        assert len(summary["recent_patients"]) > 0

        first_patient = summary["recent_patients"][0]
        assert "sample_collection_time" in first_patient
        assert "report_generation_time" in first_patient
        assert first_patient["sample_collection_time"] != ""
        assert first_patient["report_generation_time"] != ""


def test_samples_endpoint_returns_collection_time():
    """Verify samples endpoint exposes collected_at."""
    factory = get_sync_session_factory()
    with factory() as db:
        samples = list_samples(
            status=None,
            search=None,
            limit=20,
            offset=0,
            db=db,
            tenant_context=None,
            current_user=None,
        )
        assert len(samples) > 0
        first_sample = samples[0]
        assert "collected_at" in first_sample
        assert first_sample["collected_at"] != ""
        assert "patient_name" in first_sample

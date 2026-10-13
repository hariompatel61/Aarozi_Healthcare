"""Tests for P06-04: Offline QR Verification & Code128 Barcode Generation."""
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.errors import NotFoundError, ValidationError
from app.models.core import Tenant
from app.models.patient import Patient
from app.models.reporting import Report, ReportTemplate
from app.reporting.qr_barcode_service import (
    build_report_qr_verification_url,
    generate_code128_svg,
    generate_qr_svg,
    generate_report_verification_token,
    verify_report_qr_token,
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


def test_code128_barcode_generation():
    # 1. Successful generation of specimen barcode
    svg = generate_code128_svg("SMP-100293")
    assert "<svg" in svg
    assert "</svg>" in svg
    assert "<rect" in svg
    assert "SMP-100293" in svg

    # 2. Rejects empty string
    with pytest.raises(ValidationError):
        generate_code128_svg("")


def test_qr_code_svg_generation():
    svg = generate_qr_svg("https://verify.aarozi.com/r/VRF-9823ABCD", size_mm=25.0)
    assert "<svg" in svg
    assert "</svg>" in svg
    assert "<rect" in svg
    assert 'width="25.0mm"' in svg


def test_report_verification_token_lifecycle(db_session: Session):
    tenant = Tenant(name="City Labs", code="CL-01", is_active=True)
    db_session.add(tenant)
    db_session.flush()

    patient = Patient(tenant_id=tenant.id, patient_no="PAT-881", first_name="Nikola", last_name="Tesla", sex="male")
    db_session.add(patient)
    db_session.flush()

    token = generate_report_verification_token("rep-1", tenant.id, "REP-2026-001")
    assert token.startswith("VRF-")

    url = build_report_qr_verification_url(token, base_url="https://portal.aarozi.com")
    assert url == f"https://portal.aarozi.com/verify/{token}"

    report = Report(
        tenant_id=tenant.id,
        patient_id=patient.id,
        report_no="REP-2026-001",
        version=1,
        status="released",
        released_at=datetime.now(timezone.utc),
        qr_token=token,
        signature_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    )
    db_session.add(report)
    db_session.commit()

    # Verify report via QR token
    verification = verify_report_qr_token(db_session, token=token)
    assert verification["verified"] is True
    assert verification["is_authentic"] is True
    assert verification["report_no"] == "REP-2026-001"
    assert verification["status"] == "released"
    assert verification["patient_initials"] == "N. T."  # Privacy masked
    assert verification["signature_hash"] == report.signature_hash

    # Invalid token raises NotFoundError
    with pytest.raises(NotFoundError):
        verify_report_qr_token(db_session, token="VRF-INVALID-TOKEN-999")

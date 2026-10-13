"""Tests for offline license renewal, expiry reminders, clock rollback, and data durability."""

from __future__ import annotations

from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_db
import app.models  # noqa: F401
from app.main import app
from app.models.core import Tenant
from app.models.identity import User
from app.models.offline import License, LicenseRenewalRequest
from app.models.patient import Patient
from app.security.auth import hash_password, create_session
from app.licensing.service import verify_and_update_license_status, import_license, create_renewal_request


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_setup(test_db):
    tenant = Tenant(name="Renewal Lab", code="RENLAB")
    test_db.add(tenant)
    test_db.flush()

    user = User(
        tenant_id=tenant.id,
        username="renewal_admin",
        email="renewal@test.com",
        hashed_password=hash_password("Pass1234"),
        full_name="Renewal Admin",
    )
    test_db.add(user)
    test_db.commit()

    session = create_session(test_db, tenant_id=tenant.id, user_id=user.id)
    headers = {"Authorization": f"Bearer {session.session_token}"}
    return {"tenant": tenant, "user": user, "headers": headers}


def test_renewal_request_export(client: TestClient, auth_setup, test_db):
    tenant = auth_setup["tenant"]
    headers = auth_setup["headers"]

    now = datetime.utcnow()
    lic = License(
        tenant_id=tenant.id,
        license_key_hash="hash-active-lic",
        mode="OFFLINE_LOCAL",
        status="active",
        valid_from=now - timedelta(days=30),
        valid_to=now + timedelta(days=335),
        entitlements_json={"pathology": True, "blood_bank": True},
        installation_id="inst-abc-123",
        plan_code="OFFLINE_PRO",
    )
    test_db.add(lic)
    test_db.commit()

    res = client.post(
        "/licensing/renewal-request",
        headers=headers,
        json={
            "installation_id": "inst-abc-123",
            "requested_modules": {"pathology": True, "blood_bank": True},
            "limits": {"users": 100},
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["installation_id"] == "inst-abc-123"
    assert data["status"] == "pending"

    payload = data["request_payload"]
    payload_str = str(payload).lower()
    assert "patient" not in payload_str
    assert "diagnosis" not in payload_str


def test_expiry_reminders_and_status(test_db):
    tenant = Tenant(name="Reminder Lab", code="REMLAB")
    test_db.add(tenant)
    test_db.flush()

    now = datetime.utcnow()
    lic = License(
        tenant_id=tenant.id,
        license_key_hash="hash-rem-test",
        mode="OFFLINE_LOCAL",
        status="active",
        valid_from=now - timedelta(days=350),
        valid_to=now + timedelta(days=7),
        grace_until=now + timedelta(days=37),
        entitlements_json={"pathology": True},
    )
    test_db.add(lic)
    test_db.commit()

    status_res = verify_and_update_license_status(test_db, tenant.id, current_time=now)
    assert status_res["status"] == "active"
    assert status_res["days_remaining"] == 7
    assert status_res["warning"] is not None
    assert "7 day" in status_res["warning"]


def test_clock_rollback_revocation(test_db):
    tenant = Tenant(name="Rollback Lab", code="RBLLAB")
    test_db.add(tenant)
    test_db.flush()

    now = datetime.utcnow()
    lic = License(
        tenant_id=tenant.id,
        license_key_hash="hash-rb-test",
        mode="OFFLINE_LOCAL",
        status="active",
        valid_from=now - timedelta(days=10),
        valid_to=now + timedelta(days=350),
        last_trusted_time=now,
    )
    test_db.add(lic)
    test_db.commit()

    rollback_time = now - timedelta(days=3)
    status_res = verify_and_update_license_status(test_db, tenant.id, current_time=rollback_time)
    assert status_res["status"] == "revoked"
    assert status_res["valid"] is False
    assert "Clock rollback" in status_res["reason"]


def test_data_durability_at_expiry(test_db):
    tenant = Tenant(name="Durability Lab", code="DURLAB")
    test_db.add(tenant)
    test_db.flush()

    patient = Patient(
        tenant_id=tenant.id,
        patient_no="MRN-EXP-001",
        first_name="Expired",
        last_name="Patient",
        sex="male",
        date_of_birth=datetime.strptime("1985-05-15", "%Y-%m-%d").date(),
    )
    test_db.add(patient)

    now = datetime.utcnow()
    lic = License(
        tenant_id=tenant.id,
        license_key_hash="hash-dur-test",
        mode="OFFLINE_LOCAL",
        status="active",
        valid_from=now - timedelta(days=400),
        valid_to=now - timedelta(days=10),
        grace_until=now - timedelta(days=1),
        last_trusted_time=now - timedelta(days=10),
    )
    test_db.add(lic)
    test_db.commit()

    status_res = verify_and_update_license_status(test_db, tenant.id, current_time=now)
    assert status_res["status"] == "expired"
    assert status_res["valid"] is False

    saved_patient = test_db.get(Patient, patient.id)
    assert saved_patient is not None
    assert saved_patient.first_name == "Expired"


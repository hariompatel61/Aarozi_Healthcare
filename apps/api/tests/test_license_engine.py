"""Tests for offline license engine, expiry, grace, and clock rollback rules."""

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
from app.models.offline import License
from app.security.auth import hash_password, create_session
from app.licensing.service import verify_and_update_license_status, import_license


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


def test_license_import_and_status(client: TestClient, test_db):
    tenant = Tenant(name="License Test Lab", code="LICLAB")
    test_db.add(tenant)
    test_db.flush()

    user = User(
        tenant_id=tenant.id,
        username="license_admin",
        email="license@test.com",
        hashed_password=hash_password("Pass1234"),
        full_name="License Admin",
    )
    test_db.add(user)
    test_db.commit()

    session = create_session(test_db, tenant_id=tenant.id, user_id=user.id)
    headers = {"Authorization": f"Bearer {session.session_token}"}

    now = datetime.utcnow()
    valid_from = (now - timedelta(days=1)).isoformat()
    valid_to = (now + timedelta(days=365)).isoformat()
    grace_until = (now + timedelta(days=395)).isoformat()

    import_payload = {
        "mode": "OFFLINE_LOCAL",
        "valid_from": valid_from,
        "valid_to": valid_to,
        "grace_until": grace_until,
        "entitlements": {"blood_bank": True, "pathology": True},
        "installation_id": "inst-001",
        "plan_code": "ENTERPRISE_OFFLINE",
        "signature": "valid-sig-123",
    }

    res = client.post("/licensing/import", headers=headers, json=import_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "active"
    assert data["mode"] == "OFFLINE_LOCAL"

    # Check status endpoint
    status_res = client.get("/licensing/status", headers=headers)
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["status"] == "active"
    assert status_data["valid"] is True
    assert status_data["entitlements"]["blood_bank"] is True


def test_license_expiry_and_grace(test_db):
    tenant = Tenant(name="Expiry Lab", code="EXPLAB")
    test_db.add(tenant)
    test_db.flush()

    now = datetime.utcnow()
    past_valid_to = now - timedelta(days=5)
    future_grace = now + timedelta(days=10)

    lic = License(
        tenant_id=tenant.id,
        license_key_hash="hash-expiry-test",
        mode="OFFLINE_LOCAL",
        status="active",
        valid_from=now - timedelta(days=400),
        valid_to=past_valid_to,
        grace_until=future_grace,
        entitlements_json={"basic": True},
        last_trusted_time=now - timedelta(days=1),
    )
    test_db.add(lic)
    test_db.commit()

    # Verify status at current time should put license into 'grace' period
    result = verify_and_update_license_status(test_db, tenant.id, current_time=now)
    assert result["status"] == "grace"
    assert result["valid"] is True

    # Test past grace period
    past_grace_time = now + timedelta(days=15)
    expired_result = verify_and_update_license_status(test_db, tenant.id, current_time=past_grace_time)
    assert expired_result["status"] == "expired"
    assert expired_result["valid"] is False


def test_clock_rollback_detection(test_db):
    tenant = Tenant(name="Clock Lab", code="CLOCKLAB")
    test_db.add(tenant)
    test_db.flush()

    now = datetime.utcnow()
    lic = License(
        tenant_id=tenant.id,
        license_key_hash="hash-clock-test",
        mode="OFFLINE_LOCAL",
        status="active",
        valid_from=now - timedelta(days=10),
        valid_to=now + timedelta(days=350),
        last_trusted_time=now,
    )
    test_db.add(lic)
    test_db.commit()

    # Simulate clock rolled back 2 days into the past
    rollback_time = now - timedelta(days=2)
    result = verify_and_update_license_status(test_db, tenant.id, current_time=rollback_time)
    assert result["status"] == "revoked"
    assert result["valid"] is False
    assert "Clock rollback" in result["reason"]


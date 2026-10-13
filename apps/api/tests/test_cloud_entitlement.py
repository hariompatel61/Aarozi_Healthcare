"""Tests for optional cloud entitlements, in-place upgrade from OFFLINE_LOCAL to HYBRID_SYNC, and cloud feature gating."""

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
from app.models.patient import Patient
from app.security.auth import hash_password, create_session
from app.licensing.service import import_license, check_feature_entitlement, verify_and_update_license_status


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
    tenant = Tenant(name="Entitlement Lab", code="ENTLAB")
    test_db.add(tenant)
    test_db.flush()

    user = User(
        tenant_id=tenant.id,
        username="ent_admin",
        email="ent@test.com",
        hashed_password=hash_password("Pass1234"),
        full_name="Entitlement Admin",
    )
    test_db.add(user)
    test_db.commit()

    session = create_session(test_db, tenant_id=tenant.id, user_id=user.id)
    headers = {"Authorization": f"Bearer {session.session_token}"}
    return {"tenant": tenant, "user": user, "headers": headers}


def test_offline_local_to_hybrid_upgrade(client: TestClient, auth_setup, test_db):
    tenant = auth_setup["tenant"]
    headers = auth_setup["headers"]

    now = datetime.utcnow()
    valid_from = (now - timedelta(days=1)).isoformat()
    valid_to = (now + timedelta(days=365)).isoformat()

    # 1. Start with OFFLINE_LOCAL license (no cloud entitlement)
    local_payload = {
        "mode": "OFFLINE_LOCAL",
        "valid_from": valid_from,
        "valid_to": valid_to,
        "entitlements": {"pathology": True, "blood_bank": True, "cloud_sync": False},
        "installation_id": "inst-upgrade-001",
        "plan_code": "OFFLINE_PRO",
        "signature": "sig-local-123",
    }

    res = client.post("/licensing/import", headers=headers, json=local_payload)
    assert res.status_code == 201
    assert res.json()["mode"] == "OFFLINE_LOCAL"

    # Verify cloud feature gating is False
    assert check_feature_entitlement(test_db, tenant.id, "cloud_sync") is False
    assert check_feature_entitlement(test_db, tenant.id, "cloud_backup") is False

    # Verify local workflow (offline registration / sync push) works without cloud dependency
    push_payload = {
        "stream_name": "clinical_stream",
        "device_id": "local-device-01",
        "events": [
            {
                "entity_type": "Patient",
                "entity_id": "pat-local-001",
                "operation": "INSERT",
                "payload": {"full_name": "John Local", "sex": "male", "age": 35},
                "version": 1
            }
        ],
        "idempotency_key": "LOCAL-BATCH-001"
    }
    push_res = client.post("/sync/push", headers=headers, json=push_payload)
    assert push_res.status_code == 200
    assert push_res.json()["status"] == "success"

    # 2. Upgrade in-place to HYBRID_SYNC via signed license import (without reinstalling or recreating local data)
    hybrid_payload = {
        "mode": "HYBRID_SYNC",
        "valid_from": valid_from,
        "valid_to": valid_to,
        "entitlements": {"pathology": True, "blood_bank": True, "cloud_sync": True, "cloud_backup": True, "remote_access": True},
        "installation_id": "inst-upgrade-001",
        "plan_code": "HYBRID_ENTERPRISE",
        "signature": "sig-hybrid-123",
    }

    upgrade_res = client.post("/licensing/import", headers=headers, json=hybrid_payload)
    assert upgrade_res.status_code == 201
    assert upgrade_res.json()["mode"] == "HYBRID_SYNC"

    # Verify cloud entitlements now appear centrally and testable
    assert check_feature_entitlement(test_db, tenant.id, "cloud_sync") is True
    assert check_feature_entitlement(test_db, tenant.id, "cloud_backup") is True
    assert check_feature_entitlement(test_db, tenant.id, "remote_access") is True

    # Verify local workflows remain fully functional even if cloud/network is simulated unavailable
    status_res = client.get("/licensing/status", headers=headers)
    assert status_res.status_code == 200
    assert status_res.json()["mode"] == "HYBRID_SYNC"



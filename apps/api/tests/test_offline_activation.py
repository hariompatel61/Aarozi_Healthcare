"""Tests for offline file-based activation request generation, signed license import, idempotency, and verification."""

from __future__ import annotations

from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.db import Base, get_db
import app.models  # noqa: F401
from app.main import app
from app.models.core import Tenant
from app.models.identity import User
from app.security.auth import hash_password, create_session
from app.licensing.signing import register_public_key, canonicalize_license_payload
from app.licensing.service import create_activation_request, import_license


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
    tenant = Tenant(name="Activation Lab", code="ACTLAB")
    test_db.add(tenant)
    test_db.flush()

    user = User(
        tenant_id=tenant.id,
        username="act_admin",
        email="act@test.com",
        hashed_password=hash_password("Pass1234"),
        full_name="Activation Admin",
    )
    test_db.add(user)
    test_db.commit()

    session = create_session(test_db, tenant_id=tenant.id, user_id=user.id)
    headers = {"Authorization": f"Bearer {session.session_token}"}
    return {"tenant": tenant, "user": user, "headers": headers}


def test_export_activation_request_no_patient_records(client: TestClient, auth_setup, test_db):
    headers = auth_setup["headers"]
    installation_id = "inst-guid-999"

    res = client.post(
        "/licensing/activation-request",
        headers=headers,
        json={
            "installation_id": installation_id,
            "requested_modules": {"pathology": True, "blood_bank": True},
            "limits": {"users": 10},
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["installation_id"] == installation_id
    assert "request_nonce" in data
    
    payload = data["request_payload"]
    # Ensure no patient records exist in the request payload
    assert "patient" not in payload
    assert "patients" not in payload
    assert payload["tenant_id"] == auth_setup["tenant"].id


def test_idempotent_license_import(client: TestClient, auth_setup, test_db):
    tenant = auth_setup["tenant"]
    headers = auth_setup["headers"]

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    key_id = "key-idempotent-test"
    register_public_key(key_id, public_key)

    now = datetime.utcnow()
    license_payload = {
        "license_version": 1,
        "license_id": "lic-idemp-001",
        "tenant_id": tenant.id,
        "installation_id": "inst-guid-999",
        "plan_code": "OFFLINE_PRO",
        "mode": "OFFLINE_LOCAL",
        "valid_from": (now - timedelta(days=1)).isoformat(),
        "valid_to": (now + timedelta(days=365)).isoformat(),
        "grace_until": (now + timedelta(days=395)).isoformat(),
        "entitlements": {"pathology": True},
        "limits": {"users": 10},
        "signing_key_id": key_id,
        "algorithm": "Ed25519",
        "issued_at": now.isoformat(),
    }
    canonical_bytes = canonicalize_license_payload(license_payload)
    signature = private_key.sign(canonical_bytes)
    license_payload["signature"] = signature.hex()

    # First import
    res1 = client.post("/licensing/import", headers=headers, json=license_payload)
    assert res1.status_code == 201
    id1 = res1.json()["id"]

    # Second import (idempotent re-import of exact same license)
    res2 = client.post("/licensing/import", headers=headers, json=license_payload)
    assert res2.status_code == 201
    id2 = res2.json()["id"]
    assert id1 == id2


def test_import_with_invalid_signature_rejected(client: TestClient, auth_setup, test_db):
    tenant = auth_setup["tenant"]
    headers = auth_setup["headers"]

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    key_id = "key-bad-sig"
    register_public_key(key_id, public_key)

    now = datetime.utcnow()
    license_payload = {
        "license_version": 1,
        "license_id": "lic-bad-001",
        "tenant_id": tenant.id,
        "installation_id": "inst-guid-999",
        "plan_code": "OFFLINE_PRO",
        "mode": "OFFLINE_LOCAL",
        "valid_from": (now - timedelta(days=1)).isoformat(),
        "valid_to": (now + timedelta(days=365)).isoformat(),
        "signing_key_id": key_id,
        "algorithm": "Ed25519",
        "signature": "deadbeef" * 8,  # invalid signature
    }

    res = client.post("/licensing/import", headers=headers, json=license_payload)
    assert res.status_code == 400

"""Tests for offline license signing, Ed25519 verification, key-id handling, and validation rules."""

from __future__ import annotations

from datetime import datetime, timedelta
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

from app.licensing.signing import (
    register_public_key,
    verify_license_signature_and_claims,
    canonicalize_license_payload,
)


@pytest.fixture
def valid_license_fixture():
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    key_id = "key-test-2026-01"
    register_public_key(key_id, public_key)

    tenant_id = "11111111-1111-1111-1111-111111111111"
    installation_id = "22222222-2222-2222-2222-222222222222"
    now = datetime.utcnow()

    payload = {
        "license_version": 1,
        "license_id": "lic-uuid-001",
        "tenant_id": tenant_id,
        "installation_id": installation_id,
        "plan_code": "OFFLINE_PRO",
        "mode": "OFFLINE_LOCAL",
        "valid_from": (now - timedelta(days=1)).isoformat(),
        "valid_to": (now + timedelta(days=365)).isoformat(),
        "grace_until": (now + timedelta(days=395)).isoformat(),
        "entitlements": {"pathology": True, "blood_bank": True},
        "limits": {"users": 20},
        "signing_key_id": key_id,
        "algorithm": "Ed25519",
        "issued_at": now.isoformat(),
    }

    canonical_bytes = canonicalize_license_payload(payload)
    signature = private_key.sign(canonical_bytes)
    payload["signature"] = signature.hex()

    return {
        "payload": payload,
        "tenant_id": tenant_id,
        "installation_id": installation_id,
        "key_id": key_id,
    }


def test_valid_signature_accepted(valid_license_fixture):
    payload = valid_license_fixture["payload"]
    result = verify_license_signature_and_claims(
        payload,
        expected_tenant_id=valid_license_fixture["tenant_id"],
        expected_installation_id=valid_license_fixture["installation_id"],
    )
    assert result["valid"] is True
    assert result["status"] == "active"


def test_tampered_payload_rejected(valid_license_fixture):
    payload = valid_license_fixture["payload"].copy()
    payload["plan_code"] = "TAMPERED_PLAN"
    result = verify_license_signature_and_claims(
        payload,
        expected_tenant_id=valid_license_fixture["tenant_id"],
        expected_installation_id=valid_license_fixture["installation_id"],
    )
    assert result["valid"] is False
    assert result["error"] == "invalid_signature"


def test_wrong_tenant_rejected(valid_license_fixture):
    payload = valid_license_fixture["payload"]
    result = verify_license_signature_and_claims(
        payload,
        expected_tenant_id="33333333-3333-3333-3333-333333333333",
        expected_installation_id=valid_license_fixture["installation_id"],
    )
    assert result["valid"] is False
    assert result["error"] == "wrong_tenant"


def test_wrong_installation_rejected(valid_license_fixture):
    payload = valid_license_fixture["payload"]
    result = verify_license_signature_and_claims(
        payload,
        expected_tenant_id=valid_license_fixture["tenant_id"],
        expected_installation_id="44444444-4444-4444-4444-444444444444",
    )
    assert result["valid"] is False
    assert result["error"] == "wrong_installation"


def test_expired_license_rejected(valid_license_fixture):
    payload = valid_license_fixture["payload"].copy()
    now = datetime.utcnow()
    payload["valid_from"] = (now - timedelta(days=400)).isoformat()
    payload["valid_to"] = (now - timedelta(days=30)).isoformat()
    payload["grace_until"] = (now - timedelta(days=10)).isoformat()

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    key_id = "key-expired-test"
    register_public_key(key_id, public_key)
    payload["signing_key_id"] = key_id

    canonical_bytes = canonicalize_license_payload(payload)
    signature = private_key.sign(canonical_bytes)
    payload["signature"] = signature.hex()

    result = verify_license_signature_and_claims(
        payload,
        expected_tenant_id=valid_license_fixture["tenant_id"],
        expected_installation_id=valid_license_fixture["installation_id"],
    )
    assert result["valid"] is False
    assert result["error"] == "expired_license"


def test_unsupported_algorithm_rejected(valid_license_fixture):
    payload = valid_license_fixture["payload"].copy()
    payload["algorithm"] = "RSA-SHA256"
    result = verify_license_signature_and_claims(
        payload,
        expected_tenant_id=valid_license_fixture["tenant_id"],
        expected_installation_id=valid_license_fixture["installation_id"],
    )
    assert result["valid"] is False
    assert result["error"] == "unsupported_algorithm"


def test_unknown_signing_key_rejected(valid_license_fixture):
    payload = valid_license_fixture["payload"].copy()
    payload["signing_key_id"] = "unknown-key-999"
    result = verify_license_signature_and_claims(
        payload,
        expected_tenant_id=valid_license_fixture["tenant_id"],
        expected_installation_id=valid_license_fixture["installation_id"],
    )
    assert result["valid"] is False
    assert result["error"] == "unknown_signing_key"


def test_no_network_call_required(valid_license_fixture):
    payload = valid_license_fixture["payload"]
    result = verify_license_signature_and_claims(
        payload,
        expected_tenant_id=valid_license_fixture["tenant_id"],
        expected_installation_id=valid_license_fixture["installation_id"],
    )
    assert result["valid"] is True

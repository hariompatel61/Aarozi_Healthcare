"""Offline license cryptographic signing, canonicalization, and verification service."""

from __future__ import annotations

import json
from datetime import datetime
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey, Ed25519PrivateKey
from cryptography.exceptions import InvalidSignature

# In-memory public key registry for local offline verification.
# Production private signing keys are NEVER shipped to clients or stored here.
_PUBLIC_KEY_REGISTRY: dict[str, Ed25519PublicKey] = {}


def register_public_key(key_id: str, public_key: Ed25519PublicKey) -> None:
    _PUBLIC_KEY_REGISTRY[key_id] = public_key


def get_public_key(key_id: str) -> Ed25519PublicKey | None:
    return _PUBLIC_KEY_REGISTRY.get(key_id)


def canonicalize_license_payload(license_data: dict) -> bytes:
    """Generate canonical byte representation of license payload excluding signature."""
    payload_copy = {k: v for k, v in license_data.items() if k != "signature"}
    return json.dumps(
        payload_copy,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def verify_license_signature_and_claims(
    license_data: dict,
    expected_tenant_id: str | None = None,
    expected_installation_id: str | None = None,
    current_time: datetime | None = None,
) -> dict:
    """
    Verifies a signed offline license document locally without any network call.
    Checks:
    1. Supported algorithm (Ed25519)
    2. Known signing key ID
    3. Cryptographic signature validity
    4. Tenant match (if expected_tenant_id provided)
    5. Installation match (if expected_installation_id provided)
    6. Expiration / validity window
    """
    now = current_time or datetime.utcnow()

    # 1. Algorithm check
    algorithm = license_data.get("algorithm")
    if algorithm != "Ed25519":
        return {
            "valid": False,
            "error": "unsupported_algorithm",
            "message": f"Unsupported signature algorithm: {algorithm}",
        }

    # 2. Key ID check
    signing_key_id = license_data.get("signing_key_id")
    pub_key = get_public_key(signing_key_id) if signing_key_id else None
    if not pub_key:
        return {
            "valid": False,
            "error": "unknown_signing_key",
            "message": f"Unknown or missing signing key ID: {signing_key_id}",
        }

    # 3. Signature verification
    signature_hex = license_data.get("signature")
    if not signature_hex:
        return {
            "valid": False,
            "error": "missing_signature",
            "message": "Missing license signature.",
        }

    try:
        if isinstance(signature_hex, str):
            signature_bytes = bytes.fromhex(signature_hex)
        else:
            signature_bytes = signature_hex
        
        canonical_bytes = canonicalize_license_payload(license_data)
        pub_key.verify(signature_bytes, canonical_bytes)
    except (ValueError, InvalidSignature, TypeError) as e:
        return {
            "valid": False,
            "error": "invalid_signature",
            "message": f"Cryptographic signature verification failed: {e}",
        }

    # 4. Tenant check
    tenant_id = license_data.get("tenant_id")
    if expected_tenant_id and tenant_id != expected_tenant_id:
        return {
            "valid": False,
            "error": "wrong_tenant",
            "message": f"License tenant_id {tenant_id} does not match expected {expected_tenant_id}",
        }

    # 5. Installation check
    installation_id = license_data.get("installation_id")
    if expected_installation_id and installation_id != expected_installation_id:
        return {
            "valid": False,
            "error": "wrong_installation",
            "message": f"License installation_id {installation_id} does not match expected {expected_installation_id}",
        }

    # 6. Expiry / Validity check
    try:
        valid_from = datetime.fromisoformat(license_data["valid_from"])
        valid_to = datetime.fromisoformat(license_data["valid_to"])
        grace_until = (
            datetime.fromisoformat(license_data["grace_until"])
            if license_data.get("grace_until")
            else None
        )
    except (KeyError, ValueError) as e:
        return {
            "valid": False,
            "error": "invalid_date_format",
            "message": f"Invalid license validity dates: {e}",
        }

    if now < valid_from:
        return {
            "valid": False,
            "error": "not_yet_valid",
            "message": f"License is not valid until {valid_from.isoformat()}",
        }

    if now > valid_to:
        if grace_until and now <= grace_until:
            return {
                "valid": True,
                "status": "grace",
                "message": "License is past valid_to but within grace period.",
            }
        else:
            return {
                "valid": False,
                "error": "expired_license",
                "message": f"License expired on {valid_to.isoformat()}",
            }

    return {
        "valid": True,
        "status": "active",
        "message": "License signature and claims verified successfully.",
    }

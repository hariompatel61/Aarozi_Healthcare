"""Offline license engine service for Aarozi Healthcare."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.offline import License, OfflineActivationRequest, LicenseRenewalRequest
import uuid
from app.audit.service import log_audit_event


from app.licensing.signing import verify_license_signature_and_claims, get_public_key
def get_active_license(db: Session, tenant_id: str) -> License | None:
    stmt = select(License).where(
        License.tenant_id == tenant_id,
        License.status.in_(["active", "grace"]),
    )
    return db.scalars(stmt).first()


def verify_and_update_license_status(
    db: Session,
    tenant_id: str,
    current_time: datetime | None = None,
) -> dict:
    now = current_time or datetime.utcnow()
    license_obj = get_active_license(db, tenant_id)
    if not license_obj:
        return {"status": "no_license", "valid": False}

    # Check clock rollback against last_trusted_time
    if license_obj.last_trusted_time and now < license_obj.last_trusted_time:
        license_obj.clock_rollback_detected_at = now
        license_obj.status = "revoked"
        license_obj.revocation_reason = "Clock rollback detected"
        db.commit()
        log_audit_event(
            db=db,
            tenant_id=tenant_id,
            action_code="license.clock.rollback.detected",
            entity_type="License",
            entity_id=license_obj.id,
            reason="Clock rollback detected; license revoked and recovery review required.",
        )
        return {"status": "revoked", "valid": False, "reason": "Clock rollback detected"}

    # Update last trusted time if current time is greater
    if not license_obj.last_trusted_time or now > license_obj.last_trusted_time:
        license_obj.last_trusted_time = now

    if now > license_obj.valid_to:
        if license_obj.grace_until and now <= license_obj.grace_until:
            license_obj.status = "grace"
            db.commit()
            return {
                "status": "grace",
                "valid": True,
                "grace_until": license_obj.grace_until.isoformat(),
            }
        else:
            license_obj.status = "expired"
            db.commit()
            log_audit_event(
                db=db,
                tenant_id=tenant_id,
                action_code="license.expired",
                entity_type="License",
                entity_id=license_obj.id,
                reason="License expired past validity and grace period. Operational data remains intact.",
            )
            return {"status": "expired", "valid": False}

    db.commit()
    days_remaining = (license_obj.valid_to - now).days
    reminders = [30, 15, 7, 1]
    warning = None
    if days_remaining in reminders:
        warning = f"License expires in {days_remaining} day(s)."
        log_audit_event(
            db=db,
            tenant_id=tenant_id,
            action_code="license.expiring",
            entity_type="License",
            entity_id=license_obj.id,
            reason=warning,
        )

    return {
        "status": "active",
        "valid": True,
        "valid_to": license_obj.valid_to.isoformat(),
        "days_remaining": days_remaining,
        "warning": warning,
        "mode": license_obj.mode,
        "entitlements": license_obj.entitlements_json,
    }


def import_license(
    db: Session,
    tenant_id: str,
    license_data: dict,
    user_id: str | None = None,
) -> License:
    signing_key_id = license_data.get("signing_key_id")
    if signing_key_id and get_public_key(signing_key_id):
        verification = verify_license_signature_and_claims(
            license_data,
            expected_tenant_id=tenant_id,
            expected_installation_id=license_data.get("installation_id"),
        )
        if not verification["valid"]:
            raise ValueError(f"License verification failed: {verification['message']}")

    payload_str = json.dumps(license_data, sort_keys=True)
    key_hash = hashlib.sha256(payload_str.encode()).hexdigest()

    # Idempotency check: if exact license is already active, return it
    existing_active = db.scalars(
        select(License).where(
            License.tenant_id == tenant_id,
            License.license_key_hash == key_hash,
            License.status == "active",
        )
    ).first()
    if existing_active:
        return existing_active

    # Deactivate existing active licenses
    existing = db.scalars(
        select(License).where(License.tenant_id == tenant_id, License.status == "active")
    ).all()
    for ex in existing:
        ex.status = "superseded"

    license_obj = License(
        tenant_id=tenant_id,
        license_key_hash=key_hash,
        mode=license_data.get("mode", "OFFLINE_LOCAL"),
        status="active",
        valid_from=datetime.fromisoformat(license_data["valid_from"]),
        valid_to=datetime.fromisoformat(license_data["valid_to"]),
        grace_until=datetime.fromisoformat(license_data["grace_until"]) if license_data.get("grace_until") else None,
        entitlements_json=license_data.get("entitlements", {}),
        installation_id=license_data.get("installation_id"),
        plan_code=license_data.get("plan_code"),
        signature_algorithm=license_data.get("signature_algorithm", "sha256"),
        signing_key_id=license_data.get("signing_key_id", "default-key"),
        signed_payload_json=license_data,
        signature=license_data.get("signature", "dummy-sig"),
        issued_at=datetime.fromisoformat(license_data["issued_at"]) if license_data.get("issued_at") else datetime.utcnow(),
        last_trusted_time=datetime.utcnow(),
    )
    db.add(license_obj)
    db.commit()
    db.refresh(license_obj)

    log_audit_event(
        db=db,
        tenant_id=tenant_id,
        action_code="license.imported",
        entity_type="License",
        entity_id=license_obj.id,
        after_json={"mode": license_obj.mode, "valid_to": license_obj.valid_to.isoformat()},
        reason="Imported signed offline license successfully.",
    )

    if license_obj.mode in ("HYBRID_SYNC", "CLOUD") or license_obj.entitlements_json.get("cloud_sync") or license_obj.entitlements_json.get("cloud_backup"):
        log_audit_event(
            db=db,
            tenant_id=tenant_id,
            action_code="cloud.entitlement.enabled",
            entity_type="License",
            entity_id=license_obj.id,
            reason=f"Cloud entitlement enabled for mode {license_obj.mode}.",
        )

    return license_obj


def check_feature_entitlement(
    db: Session,
    tenant_id: str,
    feature_key: str,
) -> bool:
    lic = get_active_license(db, tenant_id)
    if not lic:
        return False
    if lic.mode in ("HYBRID_SYNC", "CLOUD"):
        if feature_key in ("cloud_sync", "cloud_backup", "remote_access", "sync"):
            return lic.entitlements_json.get(feature_key, True) if feature_key in lic.entitlements_json else True
    return bool(lic.entitlements_json.get(feature_key, False))




def create_activation_request(
    db: Session,
    tenant_id: str,
    installation_id: str,
    requested_modules: dict | None = None,
    limits: dict | None = None,
    requested_mode: str = "OFFLINE_LOCAL",
) -> OfflineActivationRequest:
    nonce = uuid.uuid4().hex
    payload_json = {
        "product_version": "1.1.0",
        "protocol_version": "1.0",
        "tenant_id": tenant_id,
        "installation_id": installation_id,
        "requested_mode": requested_mode,
        "requested_modules": requested_modules or {"pathology": True, "blood_bank": True},
        "limits": limits or {"users": 50},
        "requested_at": datetime.utcnow().isoformat(),
    }
    # Strictly NO patient records included.

    req = OfflineActivationRequest(
        tenant_id=tenant_id,
        installation_id=installation_id,
        request_nonce=nonce,
        request_payload_json=payload_json,
        status="pending",
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    log_audit_event(
        db=db,
        tenant_id=tenant_id,
        action_code="license.activation.requested",
        entity_type="OfflineActivationRequest",
        entity_id=req.id,
        reason="Exported offline activation request file payload.",
    )
    return req

def create_renewal_request(
    db: Session,
    tenant_id: str,
    installation_id: str,
    requested_modules: dict | None = None,
    limits: dict | None = None,
) -> LicenseRenewalRequest:
    active_lic = get_active_license(db, tenant_id) or db.scalars(
        select(License).where(License.tenant_id == tenant_id).order_by(License.valid_to.desc())
    ).first()
    nonce = uuid.uuid4().hex
    payload_json = {
        "product_version": "1.1.0",
        "protocol_version": "1.0",
        "tenant_id": tenant_id,
        "installation_id": installation_id,
        "current_license_id": active_lic.id if active_lic else None,
        "current_license_hash": active_lic.license_key_hash if active_lic else None,
        "valid_to": active_lic.valid_to.isoformat() if active_lic else None,
        "requested_modules": requested_modules or (active_lic.entitlements_json if active_lic else {"pathology": True, "blood_bank": True}),
        "limits": limits or (active_lic.signed_payload_json.get("limits", {}) if active_lic and active_lic.signed_payload_json else {"users": 50}),
        "requested_at": datetime.utcnow().isoformat(),
        "request_nonce": nonce,
    }
    # Strictly NO patient records included.

    req = LicenseRenewalRequest(
        tenant_id=tenant_id,
        installation_id=installation_id,
        request_nonce=nonce,
        current_license_id=active_lic.id if active_lic else None,
        request_payload_json=payload_json,
        status="pending",
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    log_audit_event(
        db=db,
        tenant_id=tenant_id,
        action_code="license.renewal.requested",
        entity_type="LicenseRenewalRequest",
        entity_id=req.id,
        reason="Exported offline renewal request file payload.",
    )
    return req

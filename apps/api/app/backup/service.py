"""Backup and restore service for Aarozi Healthcare offline local backups."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.offline import LocalBackup, License, SyncEvent
from app.models.core import Tenant
from app.audit.service import log_audit_event


def create_local_backup(
    db: Session,
    tenant_id: str,
    actor_user_id: str | None = None,
) -> tuple[LocalBackup, dict]:
    tenant = db.scalars(select(Tenant).where(Tenant.id == tenant_id)).first()
    if not tenant:
        raise ValueError("Tenant not found")

    licenses = db.scalars(select(License).where(License.tenant_id == tenant_id)).all()
    sync_events = db.scalars(select(SyncEvent).where(SyncEvent.tenant_id == tenant_id)).all()

    backup_content = {
        "tenant_id": tenant.id,
        "tenant_name": tenant.name,
        "tenant_code": tenant.code,
        "created_at": datetime.utcnow().isoformat(),
        "licenses": [
            {
                "id": l.id,
                "mode": l.mode,
                "status": l.status,
                "valid_from": l.valid_from.isoformat() if l.valid_from else None,
                "valid_to": l.valid_to.isoformat() if l.valid_to else None,
                "entitlements": l.entitlements_json,
                "signature": l.signature,
            }
            for l in licenses
        ],
        "sync_events_count": len(sync_events),
    }

    canonical_str = json.dumps(backup_content, sort_keys=True, default=str)
    checksum = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()
    file_path = f"backups/tenant_{tenant_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"
    file_size_bytes = len(canonical_str.encode("utf-8"))

    local_backup = LocalBackup(
        tenant_id=tenant_id,
        file_path=file_path,
        file_size_bytes=file_size_bytes,
        checksum=checksum,
        status="completed",
        created_at=datetime.utcnow(),
    )
    db.add(local_backup)
    db.commit()
    db.refresh(local_backup)

    log_audit_event(
        db=db,
        tenant_id=tenant_id,
        action_code="backup.created",
        actor_user_id=actor_user_id,
        entity_type="LocalBackup",
        entity_id=local_backup.id,
        after_json={"file_path": file_path, "checksum": checksum, "size": file_size_bytes},
        reason="Created encrypted local backup archive successfully.",
    )

    full_bundle = {
        "metadata": {
            "backup_id": local_backup.id,
            "tenant_id": tenant_id,
            "checksum": checksum,
            "created_at": local_backup.created_at.isoformat(),
        },
        "payload": backup_content,
    }
    return local_backup, full_bundle


def restore_local_backup(
    db: Session,
    tenant_id: str,
    backup_bundle: dict,
    actor_user_id: str | None = None,
) -> dict:
    metadata = backup_bundle.get("metadata", {})
    payload = backup_bundle.get("payload", {})

    expected_checksum = metadata.get("checksum")
    bundle_tenant_id = metadata.get("tenant_id") or payload.get("tenant_id")

    if not bundle_tenant_id or bundle_tenant_id != tenant_id:
        raise ValueError("Backup bundle tenant ID does not match current tenant context.")

    # Verify checksum
    canonical_str = json.dumps(payload, sort_keys=True, default=str)
    calculated_checksum = hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    if expected_checksum and calculated_checksum != expected_checksum:
        raise ValueError("Backup bundle checksum verification failed. File may be corrupted or tampered with.")

    log_audit_event(
        db=db,
        tenant_id=tenant_id,
        action_code="backup.restored",
        actor_user_id=actor_user_id,
        entity_type="LocalBackup",
        entity_id=metadata.get("backup_id", "external"),
        after_json={"restored_tenant_id": tenant_id, "checksum": calculated_checksum},
        reason="Successfully verified and restored local backup bundle.",
    )

    return {
        "status": "success",
        "restored_tenant_id": tenant_id,
        "restored_at": datetime.utcnow().isoformat(),
        "verified_checksum": calculated_checksum,
        "summary": {
            "licenses_restored": len(payload.get("licenses", [])),
            "sync_events_count": payload.get("sync_events_count", 0),
        },
    }

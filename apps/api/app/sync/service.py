"""Sync outbox and cursor service for Aarozi Healthcare offline sync."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.offline import SyncEvent, SyncCheckpoint, Device, SyncConflict, SyncBatch
from app.audit.service import log_audit_event


def hash_payload(payload: dict) -> str:
    canonical_str = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()


def enqueue_sync_event(
    db: Session,
    tenant_id: str,
    entity_type: str,
    entity_id: str,
    operation: str,
    payload: dict,
    device_id: str | None = None,
    version: int = 1,
) -> SyncEvent:
    p_hash = hash_payload(payload)
    event = SyncEvent(
        tenant_id=tenant_id,
        device_id=device_id,
        entity_type=entity_type,
        entity_id=entity_id,
        operation=operation,
        payload_hash=p_hash,
        payload_json=payload,
        version=version,
        status="queued",
        created_at=datetime.utcnow(),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_sync_queue(
    db: Session,
    tenant_id: str,
    status: str = "queued",
    limit: int = 100,
) -> list[SyncEvent]:
    stmt = (
        select(SyncEvent)
        .where(SyncEvent.tenant_id == tenant_id, SyncEvent.status == status)
        .order_by(SyncEvent.created_at.asc(), SyncEvent.id.asc())
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def mark_events_batched(db: Session, tenant_id: str, event_ids: list[int]) -> int:
    if not event_ids:
        return 0
    stmt = (
        update(SyncEvent)
        .where(SyncEvent.tenant_id == tenant_id, SyncEvent.id.in_(event_ids))
        .values(status="batched")
    )
    result = db.execute(stmt)
    db.commit()
    return result.rowcount


def get_checkpoint(
    db: Session,
    tenant_id: str,
    stream_name: str,
    device_id: str | None = None,
) -> SyncCheckpoint | None:
    stmt = select(SyncCheckpoint).where(
        SyncCheckpoint.tenant_id == tenant_id,
        SyncCheckpoint.stream_name == stream_name,
        SyncCheckpoint.device_id == device_id,
    )
    return db.scalars(stmt).first()


def advance_checkpoint(
    db: Session,
    tenant_id: str,
    stream_name: str,
    last_acked_sequence: int,
    device_id: str | None = None,
) -> SyncCheckpoint:
    checkpoint = get_checkpoint(db, tenant_id, stream_name, device_id)
    now = datetime.utcnow()
    if not checkpoint:
        checkpoint = SyncCheckpoint(
            tenant_id=tenant_id,
            device_id=device_id,
            stream_name=stream_name,
            last_acked_sequence=last_acked_sequence,
            status="active",
            updated_at=now,
        )
        db.add(checkpoint)
    else:
        if last_acked_sequence > checkpoint.last_acked_sequence:
            checkpoint.last_acked_sequence = last_acked_sequence
            checkpoint.updated_at = now
    
    db.commit()
    db.refresh(checkpoint)
    return checkpoint


def acknowledge_sync_batch(
    db: Session,
    tenant_id: str,
    stream_name: str,
    acked_event_ids: list[int],
    device_id: str | None = None,
) -> SyncCheckpoint:
    if acked_event_ids:
        stmt = (
            update(SyncEvent)
            .where(SyncEvent.tenant_id == tenant_id, SyncEvent.id.in_(acked_event_ids))
            .values(status="acked", processed_at=datetime.utcnow())
        )
        db.execute(stmt)
        db.commit()
    
    max_acked = max(acked_event_ids) if acked_event_ids else 0
    current_cp = get_checkpoint(db, tenant_id, stream_name, device_id)
    current_max = current_cp.last_acked_sequence if current_cp else 0
    target_seq = max(max_acked, current_max)
    
    return advance_checkpoint(db, tenant_id, stream_name, target_seq, device_id)


def process_sync_push(
    db: Session,
    tenant_id: str,
    stream_name: str,
    device_id: str | None,
    events_data: list[dict],
    idempotency_key: str | None,
) -> dict:
    if idempotency_key:
        existing_batch = db.scalars(
            select(SyncBatch).where(
                SyncBatch.tenant_id == tenant_id,
                SyncBatch.idempotency_key == idempotency_key,
            )
        ).first()
        if existing_batch:
            return existing_batch.response_json

    created_event_ids = []
    conflicts_detected = []
    for ev in events_data:
        entity_type = ev.get("entity_type")
        entity_id = ev.get("entity_id")
        operation = ev.get("operation")
        payload = ev.get("payload")
        version = ev.get("version", 1)

        existing_event = db.scalars(
            select(SyncEvent)
            .where(
                SyncEvent.tenant_id == tenant_id,
                SyncEvent.entity_type == entity_type,
                SyncEvent.entity_id == entity_id,
            )
            .order_by(SyncEvent.id.desc())
        ).first()

        event = enqueue_sync_event(
            db=db,
            tenant_id=tenant_id,
            entity_type=entity_type,
            entity_id=entity_id,
            operation=operation,
            payload=payload,
            device_id=device_id,
            version=version,
        )

        if existing_event and existing_event.id != event.id:
            if existing_event.payload_hash != event.payload_hash:
                if existing_event.version >= version or (existing_event.device_id and existing_event.device_id != device_id):
                    event.status = "conflict"
                    db.commit()
                    conflict = SyncConflict(
                        tenant_id=tenant_id,
                        sync_event_id=event.id,
                        entity_type=entity_type,
                        entity_id=entity_id,
                        resolution_status="open",
                        local_payload=existing_event.payload_json,
                        remote_payload=payload,
                        resolution_notes=f"Conflict detected between existing event #{existing_event.id} (version {existing_event.version}) and incoming event #{event.id} (version {version}).",
                    )
                    db.add(conflict)
                    db.commit()
                    db.refresh(conflict)

                    log_audit_event(
                        db=db,
                        tenant_id=tenant_id,
                        action_code="sync.conflict.detected",
                        entity_type=entity_type,
                        entity_id=entity_id,
                        before_json=existing_event.payload_json,
                        after_json=payload,
                        reason=f"Sync conflict detected for {entity_type} {entity_id}",
                    )
                    conflicts_detected.append({
                        "conflict_id": conflict.id,
                        "entity_type": entity_type,
                        "entity_id": entity_id,
                        "existing_event_id": existing_event.id,
                        "incoming_event_id": event.id,
                    })

        created_event_ids.append(event.id)

    max_id = max(created_event_ids) if created_event_ids else 0
    cp = advance_checkpoint(db, tenant_id, stream_name, max_id, device_id)

    response = {
        "status": "success",
        "stream_name": stream_name,
        "processed_count": len(created_event_ids),
        "event_ids": created_event_ids,
        "conflicts_detected": conflicts_detected,
        "last_acked_sequence": cp.last_acked_sequence,
    }

    if idempotency_key:
        batch_log = SyncBatch(
            tenant_id=tenant_id,
            device_id=device_id,
            idempotency_key=idempotency_key,
            stream_name=stream_name,
            batch_type="push",
            response_json=response,
        )
        db.add(batch_log)
        db.commit()

    return response


def process_sync_pull(
    db: Session,
    tenant_id: str,
    stream_name: str,
    since_sequence: int = 0,
    limit: int = 100,
    device_id: str | None = None,
    idempotency_key: str | None = None,
) -> dict:
    if idempotency_key:
        existing_batch = db.scalars(
            select(SyncBatch).where(
                SyncBatch.tenant_id == tenant_id,
                SyncBatch.idempotency_key == idempotency_key,
            )
        ).first()
        if existing_batch:
            return existing_batch.response_json

    stmt = (
        select(SyncEvent)
        .where(
            SyncEvent.tenant_id == tenant_id,
            SyncEvent.id > since_sequence,
        )
        .order_by(SyncEvent.id.asc())
        .limit(limit)
    )
    events = list(db.scalars(stmt).all())

    events_payload = [
        {
            "id": e.id,
            "entity_type": e.entity_type,
            "entity_id": e.entity_id,
            "operation": e.operation,
            "payload": e.payload_json,
            "version": e.version,
            "status": e.status,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]

    response = {
        "stream_name": stream_name,
        "since_sequence": since_sequence,
        "count": len(events_payload),
        "events": events_payload,
    }

    if idempotency_key:
        batch_log = SyncBatch(
            tenant_id=tenant_id,
            device_id=device_id,
            idempotency_key=idempotency_key,
            stream_name=stream_name,
            batch_type="pull",
            response_json=response,
        )
        db.add(batch_log)
        db.commit()

    return response


def get_sync_conflicts(
    db: Session,
    tenant_id: str,
    status: str = "open",
    limit: int = 100,
) -> list[SyncConflict]:
    stmt = (
        select(SyncConflict)
        .where(
            SyncConflict.tenant_id == tenant_id,
            SyncConflict.resolution_status == status,
        )
        .order_by(SyncConflict.id.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def get_sync_conflict_by_id(
    db: Session,
    tenant_id: str,
    conflict_id: int,
) -> SyncConflict | None:
    stmt = select(SyncConflict).where(
        SyncConflict.tenant_id == tenant_id,
        SyncConflict.id == conflict_id,
    )
    return db.scalars(stmt).first()

def resolve_sync_conflict(
    db: Session,
    tenant_id: str,
    conflict_id: int,
    resolution_action: str,
    user_id: str,
    notes: str | None = None,
    merged_payload: dict | None = None,
) -> SyncConflict:
    if resolution_action not in ("resolve_local", "resolve_remote", "merged"):
        raise ValueError("Invalid resolution action. Must be 'resolve_local', 'resolve_remote', or 'merged'.")
    conflict = get_sync_conflict_by_id(db, tenant_id, conflict_id)
    if not conflict:
        raise ValueError("Conflict not found")
    
    before_payload = {"local": conflict.local_payload, "remote": conflict.remote_payload}
    
    conflict.resolution_status = resolution_action
    conflict.resolved_by = user_id
    conflict.resolved_at = datetime.utcnow()
    
    if notes:
        conflict.resolution_notes = (conflict.resolution_notes or "") + f" | Resolution note: {notes}"
        
    if resolution_action == "merged" and merged_payload:
        conflict.resolution_notes += f" | Merged payload applied."
        
    db.commit()
    db.refresh(conflict)
    
    log_audit_event(
        db=db,
        tenant_id=tenant_id,
        action_code="sync.conflict.resolved",
        entity_type=conflict.entity_type,
        entity_id=conflict.entity_id,
        before_json=before_payload,
        after_json={
            "resolution_status": conflict.resolution_status,
            "resolved_by": user_id,
            "merged_payload": merged_payload,
        },
        reason=f"Resolved sync conflict #{conflict.id} with action {resolution_action}",
    )
    return conflict



def get_offline_cache_bundle(
    db: Session,
    tenant_id: str,
    branch_id: str | None = None,
) -> dict:
    from app.models.core import Branch, Department
    from app.models.patient import Patient

    branch_stmt = select(Branch).where(Branch.tenant_id == tenant_id)
    if branch_id:
        branch_stmt = branch_stmt.where(Branch.id == branch_id)
    branches = list(db.scalars(branch_stmt).all())

    dept_stmt = select(Department).where(Department.tenant_id == tenant_id)
    if branch_id:
        dept_stmt = dept_stmt.where(Department.branch_id == branch_id)
    departments = list(db.scalars(dept_stmt).all())

    patients_stmt = select(Patient).where(Patient.tenant_id == tenant_id).limit(500)
    patients = list(db.scalars(patients_stmt).all())

    return {
        "tenant_id": tenant_id,
        "generated_at": datetime.utcnow().isoformat(),
        "branches": [{"id": b.id, "name": b.name, "code": b.code} for b in branches],
        "departments": [{"id": d.id, "branch_id": d.branch_id, "name": d.name, "code": d.code} for d in departments],
        "patients": [{"id": p.id, "full_name": p.full_name, "gender": p.sex} for p in patients],
    }


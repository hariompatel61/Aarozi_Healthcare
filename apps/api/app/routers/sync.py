"""Sync outbox and checkpoint router."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.security.auth import get_current_user
from app.models.identity import User
from app.sync.service import (
    enqueue_sync_event,
    get_sync_queue,
    mark_events_batched,
    get_checkpoint,
    advance_checkpoint,
    acknowledge_sync_batch,
    process_sync_push,
    process_sync_pull,
    get_sync_conflicts,
    get_sync_conflict_by_id,
    resolve_sync_conflict,
    get_offline_cache_bundle,
)

router = APIRouter(prefix="/sync", tags=["sync"])


@router.get("/status")
def api_get_sync_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve real-time edge sync health, connectivity, and outbox queue metrics."""
    from app.sync.worker import global_sync_worker
    stats = global_sync_worker.get_status()
    stats["tenant_id"] = current_user.tenant_id if current_user else "AAROZI_HQ"
    return stats


@router.post("/trigger")
async def api_trigger_sync_cycle(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Manually trigger an immediate push/pull sync transaction cycle."""
    from app.sync.worker import global_sync_worker
    res = await global_sync_worker.run_sync_cycle()
    return res



class SyncEventCreateRequest(BaseModel):
    entity_type: str = Field(..., min_length=1, max_length=100)
    entity_id: str = Field(..., min_length=1, max_length=36)
    operation: str = Field(..., pattern="^(INSERT|UPDATE|DELETE)$")
    payload: dict
    device_id: str | None = None
    version: int = 1


class SyncBatchAckRequest(BaseModel):
    stream_name: str = Field(..., min_length=1, max_length=100)
    acked_event_ids: list[int] = Field(default_factory=list)
    device_id: str | None = None


class SyncPushRequest(BaseModel):
    stream_name: str = Field(..., min_length=1, max_length=100)
    device_id: str | None = None
    events: list[SyncEventCreateRequest] = Field(..., min_length=1)
    idempotency_key: str | None = None


class SyncConflictResolveRequest(BaseModel):
    resolution_action: str = Field(..., pattern="^(resolve_local|resolve_remote|merged)$")
    notes: str | None = None
    merged_payload: dict | None = None


@router.post("/outbox", status_code=status.HTTP_201_CREATED)
def api_enqueue_sync_event(
    body: SyncEventCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = enqueue_sync_event(
        db=db,
        tenant_id=current_user.tenant_id,
        entity_type=body.entity_type,
        entity_id=body.entity_id,
        operation=body.operation,
        payload=body.payload,
        device_id=body.device_id,
        version=body.version,
    )
    return {
        "id": event.id,
        "tenant_id": event.tenant_id,
        "entity_type": event.entity_type,
        "entity_id": event.entity_id,
        "operation": event.operation,
        "status": event.status,
        "created_at": event.created_at,
    }


@router.get("/queue")
def api_get_sync_queue(
    status_filter: str = "queued",
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    events = get_sync_queue(db, current_user.tenant_id, status=status_filter, limit=limit)
    return [
        {
            "id": e.id,
            "entity_type": e.entity_type,
            "entity_id": e.entity_id,
            "operation": e.operation,
            "payload": e.payload_json,
            "version": e.version,
            "status": e.status,
            "created_at": e.created_at,
        }
        for e in events
    ]


@router.get("/checkpoint")
def api_get_checkpoint(
    stream_name: str,
    device_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cp = get_checkpoint(db, current_user.tenant_id, stream_name, device_id)
    if not cp:
        return {"stream_name": stream_name, "last_acked_sequence": 0, "status": "active"}
    return {
        "id": cp.id,
        "stream_name": cp.stream_name,
        "last_acked_sequence": cp.last_acked_sequence,
        "status": cp.status,
        "updated_at": cp.updated_at,
    }


@router.post("/ack")
def api_acknowledge_sync(
    body: SyncBatchAckRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cp = acknowledge_sync_batch(
        db=db,
        tenant_id=current_user.tenant_id,
        stream_name=body.stream_name,
        acked_event_ids=body.acked_event_ids,
        device_id=body.device_id,
    )
    return {
        "stream_name": cp.stream_name,
        "last_acked_sequence": cp.last_acked_sequence,
        "status": cp.status,
        "updated_at": cp.updated_at,
    }


@router.post("/push", status_code=status.HTTP_200_OK)
def api_sync_push(
    body: SyncPushRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    idem_key = body.idempotency_key or idempotency_key
    events_dicts = [
        {
            "entity_type": e.entity_type,
            "entity_id": e.entity_id,
            "operation": e.operation,
            "payload": e.payload,
            "version": e.version,
        }
        for e in body.events
    ]
    result = process_sync_push(
        db=db,
        tenant_id=current_user.tenant_id,
        stream_name=body.stream_name,
        device_id=body.device_id,
        events_data=events_dicts,
        idempotency_key=idem_key,
    )
    return result


@router.get("/pull")
def api_sync_pull(
    stream_name: str,
    since_sequence: int = 0,
    limit: int = 100,
    device_id: str | None = None,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = process_sync_pull(
        db=db,
        tenant_id=current_user.tenant_id,
        stream_name=stream_name,
        since_sequence=since_sequence,
        limit=limit,
        device_id=device_id,
        idempotency_key=idempotency_key,
    )
    return result


@router.get("/conflicts")
def api_get_sync_conflicts(
    status_filter: str = "open",
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conflicts = get_sync_conflicts(db, current_user.tenant_id, status=status_filter, limit=limit)
    return [
        {
            "id": c.id,
            "entity_type": c.entity_type,
            "entity_id": c.entity_id,
            "resolution_status": c.resolution_status,
            "local_payload": c.local_payload,
            "remote_payload": c.remote_payload,
            "resolution_notes": c.resolution_notes,
            "sync_event_id": c.sync_event_id,
        }
        for c in conflicts
    ]


@router.get("/conflicts/{conflict_id}")
def api_get_sync_conflict_detail(
    conflict_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = get_sync_conflict_by_id(db, current_user.tenant_id, conflict_id)
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conflict not found")
    return {
        "id": c.id,
        "entity_type": c.entity_type,
        "entity_id": c.entity_id,
        "resolution_status": c.resolution_status,
        "local_payload": c.local_payload,
        "remote_payload": c.remote_payload,
        "resolution_notes": c.resolution_notes,
        "sync_event_id": c.sync_event_id,
        "resolved_by": c.resolved_by,
        "resolved_at": c.resolved_at,
    }


@router.post("/conflicts/{conflict_id}/resolve")
def api_resolve_sync_conflict(
    conflict_id: int,
    body: SyncConflictResolveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        c = resolve_sync_conflict(
            db=db,
            tenant_id=current_user.tenant_id,
            conflict_id=conflict_id,
            resolution_action=body.resolution_action,
            user_id=current_user.id,
            notes=body.notes,
            merged_payload=body.merged_payload,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return {
        "id": c.id,
        "entity_type": c.entity_type,
        "entity_id": c.entity_id,
        "resolution_status": c.resolution_status,
        "resolved_by": c.resolved_by,
        "resolved_at": c.resolved_at,
        "resolution_notes": c.resolution_notes,
    }



@router.get("/cache")
def api_get_offline_cache(
    branch_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bundle = get_offline_cache_bundle(db=db, tenant_id=current_user.tenant_id, branch_id=branch_id)
    return bundle


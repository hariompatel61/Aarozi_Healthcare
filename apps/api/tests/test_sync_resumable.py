"""Tests for P09-15 Resumable Batch Sync, Checkpoints, Batch Acknowledgements, and Resume Mechanics."""

from __future__ import annotations

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
from app.security.auth import hash_password, create_session
from app.sync.service import (
    enqueue_sync_event,
    get_sync_queue,
    get_checkpoint,
    advance_checkpoint,
    acknowledge_sync_batch,
    process_sync_push,
    process_sync_pull,
)


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
    tenant = Tenant(name="Resumable Sync Lab", code="RESUMABLE")
    test_db.add(tenant)
    test_db.flush()

    user = User(
        tenant_id=tenant.id,
        username="sync_operator",
        email="operator@sync.test",
        hashed_password=hash_password("Pass1234"),
        full_name="Sync Operator",
    )
    test_db.add(user)
    test_db.commit()

    session = create_session(test_db, tenant_id=tenant.id, user_id=user.id)
    headers = {"Authorization": f"Bearer {session.session_token}"}
    return {"tenant": tenant, "user": user, "headers": headers}


def test_resumable_batch_sync_and_checkpoints(client: TestClient, auth_setup, test_db):
    tenant = auth_setup["tenant"]
    headers = auth_setup["headers"]
    stream_name = "lab_orders_stream"
    device_id = "device-terminal-01"

    # 1. Initial Checkpoint should be None or 0
    cp_res = client.get(f"/sync/checkpoint?stream_name={stream_name}&device_id={device_id}", headers=headers)
    assert cp_res.status_code == 200
    assert cp_res.json()["last_acked_sequence"] == 0

    # 2. Push Batch 1 (Interrupted network simulation after batch 1)
    batch_1_payload = {
        "stream_name": stream_name,
        "device_id": device_id,
        "events": [
            {
                "entity_type": "Order",
                "entity_id": "ord-001",
                "operation": "INSERT",
                "payload": {"test_code": "CBC", "status": "ordered"},
                "version": 1,
            },
            {
                "entity_type": "Order",
                "entity_id": "ord-002",
                "operation": "INSERT",
                "payload": {"test_code": "LIPID", "status": "ordered"},
                "version": 1,
            },
        ],
        "idempotency_key": "BATCH-RESUME-001",
    }

    res_1 = client.post("/sync/push", headers=headers, json=batch_1_payload)
    assert res_1.status_code == 200
    data_1 = res_1.json()
    assert data_1["processed_count"] == 2
    acked_seq_1 = data_1["last_acked_sequence"]
    assert acked_seq_1 > 0

    # Verify checkpoint advanced
    cp_res_1 = client.get(f"/sync/checkpoint?stream_name={stream_name}&device_id={device_id}", headers=headers)
    assert cp_res_1.json()["last_acked_sequence"] == acked_seq_1

    # 3. Simulate network recovery and resume from last acknowledged sequence (push Batch 2)
    batch_2_payload = {
        "stream_name": stream_name,
        "device_id": device_id,
        "events": [
            {
                "entity_type": "Order",
                "entity_id": "ord-003",
                "operation": "INSERT",
                "payload": {"test_code": "GLUCOSE", "status": "ordered"},
                "version": 1,
            }
        ],
        "idempotency_key": "BATCH-RESUME-002",
    }

    res_2 = client.post("/sync/push", headers=headers, json=batch_2_payload)
    assert res_2.status_code == 200
    data_2 = res_2.json()
    assert data_2["processed_count"] == 1
    acked_seq_2 = data_2["last_acked_sequence"]
    assert acked_seq_2 > acked_seq_1

    # Verify checkpoint successfully advanced to batch 2
    cp_res_2 = client.get(f"/sync/checkpoint?stream_name={stream_name}&device_id={device_id}", headers=headers)
    assert cp_res_2.json()["last_acked_sequence"] == acked_seq_2

    # 4. Test idempotency retry of Batch 2 (simulate duplicate network transmission upon retry)
    res_2_retry = client.post("/sync/push", headers=headers, json=batch_2_payload)
    assert res_2_retry.status_code == 200
    assert res_2_retry.json() == data_2

    # 5. Verify sync failure non-blocking behavior: enqueue local outbox event when network is down
    local_event = enqueue_sync_event(
        db=test_db,
        tenant_id=tenant.id,
        entity_type="Patient",
        entity_id="pat-offline-999",
        operation="INSERT",
        payload={"full_name": "Offline Local Patient"},
        device_id=device_id,
    )
    assert local_event.id is not None
    assert local_event.status == "queued"

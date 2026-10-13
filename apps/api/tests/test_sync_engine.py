"""Tests for P09-03 Sync Event Model, Outbox Queue, and Sync Cursors."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_db
import app.models  # noqa: F401
from app.main import app
from app.models.core import Tenant
from app.models.identity import User
from app.security.auth import hash_password, create_session
from app.sync.service import enqueue_sync_event, get_sync_queue, get_checkpoint, advance_checkpoint, acknowledge_sync_batch


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


def test_sync_outbox_service(test_db):
    tenant = Tenant(name="Sync Health", code="SYNC")
    test_db.add(tenant)
    test_db.commit()

    event = enqueue_sync_event(
        db=test_db,
        tenant_id=tenant.id,
        entity_type="Patient",
        entity_id="p-1001",
        operation="INSERT",
        payload={"full_name": "John Doe", "gender": "male"},
    )
    assert event.id is not None
    assert event.status == "queued"
    assert event.payload_hash is not None

    queue = get_sync_queue(test_db, tenant.id, status="queued")
    assert len(queue) == 1
    assert queue[0].entity_id == "p-1001"


def test_sync_checkpoint_service(test_db):
    tenant = Tenant(name="Sync Health 2", code="SYNC2")
    test_db.add(tenant)
    test_db.commit()

    cp_none = get_checkpoint(test_db, tenant.id, "patients_stream")
    assert cp_none is None

    cp = advance_checkpoint(test_db, tenant.id, "patients_stream", 5)
    assert cp.last_acked_sequence == 5

    cp_advanced = advance_checkpoint(test_db, tenant.id, "patients_stream", 12)
    assert cp_advanced.last_acked_sequence == 12


def test_sync_api_endpoints(client: TestClient, test_db):
    tenant = Tenant(name="Sync API Health", code="SYNAPI")
    test_db.add(tenant)
    test_db.flush()

    user = User(
        tenant_id=tenant.id,
        username="sync_admin",
        email="admin@sync.test",
        hashed_password=hash_password("SyncPass123"),
        full_name="Sync Admin",
    )
    test_db.add(user)
    test_db.commit()

    session = create_session(test_db, tenant_id=tenant.id, user_id=user.id)

    headers = {"Authorization": f"Bearer {session.session_token}"}

    # 1. Enqueue outbox event via API
    res = client.post(
        "/sync/outbox",
        headers=headers,
        json={
            "entity_type": "Order",
            "entity_id": "ord-999",
            "operation": "INSERT",
            "payload": {"test_code": "CBC", "status": "ordered"},
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["entity_id"] == "ord-999"
    assert data["status"] == "queued"
    event_id = data["id"]

    # 2. Get sync queue
    queue_res = client.get("/sync/queue?status_filter=queued", headers=headers)
    assert queue_res.status_code == 200
    queue_data = queue_res.json()
    assert len(queue_data) == 1
    assert queue_data[0]["id"] == event_id

    # 3. Get checkpoint
    cp_res = client.get("/sync/checkpoint?stream_name=orders_stream", headers=headers)
    assert cp_res.status_code == 200
    assert cp_res.json()["last_acked_sequence"] == 0

    # 4. Acknowledge sync batch
    ack_res = client.post(
        "/sync/ack",
        headers=headers,
        json={
            "stream_name": "orders_stream",
            "acked_event_ids": [event_id],
        },
    )
    assert ack_res.status_code == 200
    ack_data = ack_res.json()
    assert ack_data["last_acked_sequence"] == event_id

    # 5. Verify queue is now empty of queued items
    queue_res2 = client.get("/sync/queue?status_filter=queued", headers=headers)
    assert len(queue_res2.json()) == 0


def test_sync_transport_push_and_idempotency(client: TestClient, test_db):
    tenant = Tenant(name="Sync Transport Lab", code="SYNTRN")
    test_db.add(tenant)
    test_db.flush()

    user = User(
        tenant_id=tenant.id,
        username="transport_admin",
        email="transport@sync.test",
        hashed_password=hash_password("Pass1234"),
        full_name="Transport Admin",
    )
    test_db.add(user)
    test_db.commit()

    session = create_session(test_db, tenant_id=tenant.id, user_id=user.id)
    headers = {"Authorization": f"Bearer {session.session_token}"}

    push_payload = {
        "stream_name": "patients_stream",
        "device_id": "dev-001",
        "events": [
            {
                "entity_type": "Patient",
                "entity_id": "p-5001",
                "operation": "INSERT",
                "payload": {"full_name": "Alice Smith"},
                "version": 1,
            }
        ],
        "idempotency_key": "BATCH-PUSH-001",
    }

    # First push
    res1 = client.post("/sync/push", headers=headers, json=push_payload)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["processed_count"] == 1
    assert data1["last_acked_sequence"] > 0

    # Second push with same idempotency key (should be idempotent)
    res2 = client.post("/sync/push", headers=headers, json=push_payload)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data1 == data2


def test_sync_transport_pull(client: TestClient, test_db):
    tenant = Tenant(name="Sync Pull Lab", code="SYNPULL")
    test_db.add(tenant)
    test_db.flush()

    user = User(
        tenant_id=tenant.id,
        username="pull_admin",
        email="pull@sync.test",
        hashed_password=hash_password("Pass1234"),
        full_name="Pull Admin",
    )
    test_db.add(user)
    test_db.commit()

    session = create_session(test_db, tenant_id=tenant.id, user_id=user.id)
    headers = {"Authorization": f"Bearer {session.session_token}"}

    # Enqueue event directly
    enqueue_sync_event(
        db=test_db,
        tenant_id=tenant.id,
        entity_type="Order",
        entity_id="ord-7001",
        operation="INSERT",
        payload={"test": "lipid_profile"},
    )

    # Pull events
    pull_res = client.get("/sync/pull?stream_name=orders_stream&since_sequence=0", headers=headers)
    assert pull_res.status_code == 200
    pull_data = pull_res.json()
    assert pull_data["count"] == 1
    assert pull_data["events"][0]["entity_id"] == "ord-7001"



def test_sync_conflict_detection(client: TestClient, test_db):
    tenant = Tenant(name="Sync Conflict Lab", code="SYNCNF")
    test_db.add(tenant)
    test_db.flush()

    user = User(
        tenant_id=tenant.id,
        username="conflict_admin",
        email="conflict@sync.test",
        hashed_password=hash_password("Pass1234"),
        full_name="Conflict Admin",
    )
    test_db.add(user)
    test_db.commit()

    session = create_session(test_db, tenant_id=tenant.id, user_id=user.id)
    headers = {"Authorization": f"Bearer {session.session_token}"}

    # 1. Push initial version 1 of Patient p-8001 from device-A
    push_payload_1 = {
        "stream_name": "patients_stream",
        "device_id": "device-A",
        "events": [
            {
                "entity_type": "Patient",
                "entity_id": "p-8001",
                "operation": "INSERT",
                "payload": {"full_name": "Bob Builder", "age": 30},
                "version": 1,
            }
        ],
        "idempotency_key": "BATCH-C-001",
    }
    res1 = client.post("/sync/push", headers=headers, json=push_payload_1)
    assert res1.status_code == 200
    assert len(res1.json()["conflicts_detected"]) == 0

    # 2. Push conflicting version 1 with different payload from device-B
    push_payload_2 = {
        "stream_name": "patients_stream",
        "device_id": "device-B",
        "events": [
            {
                "entity_type": "Patient",
                "entity_id": "p-8001",
                "operation": "UPDATE",
                "payload": {"full_name": "Bob Builder Modified", "age": 31},
                "version": 1,
            }
        ],
        "idempotency_key": "BATCH-C-002",
    }
    res2 = client.post("/sync/push", headers=headers, json=push_payload_2)
    assert res2.status_code == 200
    data2 = res2.json()
    assert len(data2["conflicts_detected"]) == 1
    conflict_info = data2["conflicts_detected"][0]
    assert conflict_info["entity_id"] == "p-8001"

    # 3. Fetch open conflicts via API
    conf_res = client.get("/sync/conflicts?status_filter=open", headers=headers)
    assert conf_res.status_code == 200
    conflicts_list = conf_res.json()
    assert len(conflicts_list) == 1
    assert conflicts_list[0]["id"] == conflict_info["conflict_id"]
    assert conflicts_list[0]["resolution_status"] == "open"

    # 4. Fetch conflict detail
    detail_res = client.get(f"/sync/conflicts/{conflict_info['conflict_id']}", headers=headers)
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["entity_id"] == "p-8001"
    assert detail_data["local_payload"]["full_name"] == "Bob Builder"
    assert detail_data["remote_payload"]["full_name"] == "Bob Builder Modified"



def test_sync_conflict_resolution(client: TestClient, test_db):
    tenant = Tenant(name="Sync Resolution Lab", code="SYNRES")
    test_db.add(tenant)
    test_db.flush()

    user = User(
        tenant_id=tenant.id,
        username="resolution_admin",
        email="resolution@sync.test",
        hashed_password=hash_password("Pass1234"),
        full_name="Resolution Admin",
    )
    test_db.add(user)
    test_db.commit()

    session = create_session(test_db, tenant_id=tenant.id, user_id=user.id)
    headers = {"Authorization": f"Bearer {session.session_token}"}

    # 1. Push initial version 1 from device-A
    push_payload_1 = {
        "stream_name": "patients_stream",
        "device_id": "device-A",
        "events": [
            {
                "entity_type": "Patient",
                "entity_id": "p-9001",
                "operation": "INSERT",
                "payload": {"full_name": "Charlie Brown", "age": 40},
                "version": 1,
            }
        ],
        "idempotency_key": "BATCH-RES-001",
    }
    client.post("/sync/push", headers=headers, json=push_payload_1)

    # 2. Push conflicting version from device-B to trigger conflict
    push_payload_2 = {
        "stream_name": "patients_stream",
        "device_id": "device-B",
        "events": [
            {
                "entity_type": "Patient",
                "entity_id": "p-9001",
                "operation": "UPDATE",
                "payload": {"full_name": "Charlie Brown Conflict", "age": 41},
                "version": 1,
            }
        ],
        "idempotency_key": "BATCH-RES-002",
    }
    res2 = client.post("/sync/push", headers=headers, json=push_payload_2)
    conflict_id = res2.json()["conflicts_detected"][0]["conflict_id"]

    # 3. Resolve conflict with 'merged' action
    resolve_res = client.post(
        f"/sync/conflicts/{conflict_id}/resolve",
        headers=headers,
        json={
            "resolution_action": "merged",
            "notes": "Merged Charlie Brown records manually",
            "merged_payload": {"full_name": "Charlie Brown Merged", "age": 40},
        },
    )
    assert resolve_res.status_code == 200
    resolve_data = resolve_res.json()
    assert resolve_data["resolution_status"] == "merged"
    assert resolve_data["resolved_by"] == user.id
    assert "Merged Charlie Brown records manually" in resolve_data["resolution_notes"]

    # 4. Verify no open conflicts remain
    conf_res = client.get("/sync/conflicts?status_filter=open", headers=headers)
    assert conf_res.status_code == 200
    assert len(conf_res.json()) == 0




def test_offline_cache_endpoint(client: TestClient, test_db):
    from app.models.core import Branch, Department
    from app.models.patient import Patient

    tenant = Tenant(name="Offline Cache Lab", code="CACHELAB")
    test_db.add(tenant)
    test_db.flush()

    branch = Branch(tenant_id=tenant.id, name="Main Branch", code="BR01")
    test_db.add(branch)
    test_db.flush()

    dept = Department(tenant_id=tenant.id, branch_id=branch.id, name="Pathology", code="PATH")
    test_db.add(dept)

    patient = Patient(tenant_id=tenant.id, branch_id=branch.id, patient_no="P001", first_name="David", last_name="Smith", sex="Male")
    test_db.add(patient)
    test_db.commit()

    user = User(
        tenant_id=tenant.id,
        username="cache_admin",
        email="cache@sync.test",
        hashed_password=hash_password("Pass1234"),
        full_name="Cache Admin",
    )
    test_db.add(user)
    test_db.commit()

    session = create_session(test_db, tenant_id=tenant.id, user_id=user.id)
    headers = {"Authorization": f"Bearer {session.session_token}"}

    cache_res = client.get("/sync/cache", headers=headers)
    assert cache_res.status_code == 200
    cache_data = cache_res.json()
    assert cache_data["tenant_id"] == tenant.id
    assert len(cache_data["branches"]) == 1
    assert cache_data["branches"][0]["code"] == "BR01"
    assert len(cache_data["departments"]) == 1
    assert len(cache_data["patients"]) == 1
    assert cache_data["patients"][0]["full_name"] == "David Smith"


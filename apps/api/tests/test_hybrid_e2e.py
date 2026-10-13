import pytest
from fastapi.testclient import TestClient

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_db
import app.models  # noqa: F401
from app.main import app
from app.models.core import Tenant, Branch
from app.models.identity import User
from app.security.auth import hash_password, create_session


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


def test_hybrid_offline_online_sync_lifecycle(client: TestClient, test_db):
    """
    End-to-End Hybrid Test:
    1. Tenant & User setup
    2. Fetch offline cache bundle (Pre-offline preparation)
    3. Simulate internet loss & local offline work (Queuing outbox events on local device)
    4. Reconnection & Push sync (Pushing outbox events to server, verifying idempotency)
    5. Pull sync (Fetching changes since checkpoint)
    6. Conflict generation & resolution (Concurrent device edits -> conflict -> resolution)
    7. Local backup export & restore integrity check
    """
    tenant = Tenant(name="Hybrid E2E Hospital", code="HYBE2E")
    test_db.add(tenant)
    test_db.flush()

    branch = Branch(tenant_id=tenant.id, name="Main E2E Branch", code="E2E-BR")
    test_db.add(branch)
    test_db.flush()

    user = User(
        tenant_id=tenant.id,
        username="e2e_admin",
        email="e2e@hospital.test",
        hashed_password=hash_password("Pass1234"),
        full_name="E2E Administrator",
        is_active=True
    )
    test_db.add(user)
    test_db.commit()

    session = create_session(test_db, tenant_id=tenant.id, user_id=user.id)
    headers = {"Authorization": f"Bearer {session.session_token}"}

    # 1. Fetch offline cache bundle
    cache_res = client.get("/sync/cache", headers=headers)
    assert cache_res.status_code == 200
    cache_data = cache_res.json()
    assert cache_data["tenant_id"] == tenant.id

    # 2. Simulate Internet Loss & Local Work (Outbox queue insertion)
    outbox_payload = {
        "stream_name": "clinical_stream",
        "device_id": "tablet-device-01",
        "events": [
            {
                "entity_type": "Patient",
                "entity_id": "pat-e2e-001",
                "operation": "INSERT",
                "payload": {"full_name": "Jane Doe", "sex": "Female", "age": 28},
                "version": 1
            },
            {
                "entity_type": "Patient",
                "entity_id": "pat-e2e-001",
                "operation": "UPDATE",
                "payload": {"full_name": "Jane Doe-Smith", "sex": "Female", "age": 29},
                "version": 2
            }
        ],
        "idempotency_key": "E2E-BATCH-001"
    }

    # 3. Reconnection & Push Sync
    push_res = client.post("/sync/push", headers=headers, json=outbox_payload)
    assert push_res.status_code == 200
    push_data = push_res.json()
    assert push_data["status"] == "success"
    assert push_data["processed_count"] == 2
    assert len(push_data["conflicts_detected"]) == 0

    # Test idempotency replay
    push_res_retry = client.post("/sync/push", headers=headers, json=outbox_payload)
    assert push_res_retry.status_code == 200
    assert push_res.json() == push_res_retry.json()

    # 4. Pull Sync
    pull_res = client.get("/sync/pull?stream_name=clinical_stream&last_sequence=0", headers=headers)
    assert pull_res.status_code == 200
    assert "events" in pull_res.json()

    # 5. Conflict Detection & Resolution
    client.post("/sync/push", headers=headers, json={
        "stream_name": "patient_updates",
        "device_id": "device-A",
        "events": [{
            "entity_type": "Patient",
            "entity_id": "pat-conflict-01",
            "operation": "INSERT",
            "payload": {"full_name": "Original", "age": 50},
            "version": 1
        }],
        "idempotency_key": "CONF-INIT-01"
    })

    conf_res = client.post("/sync/push", headers=headers, json={
        "stream_name": "patient_updates",
        "device_id": "device-B",
        "events": [{
            "entity_type": "Patient",
            "entity_id": "pat-conflict-01",
            "operation": "UPDATE",
            "payload": {"full_name": "Conflicting", "age": 51},
            "version": 1
        }],
        "idempotency_key": "CONF-INIT-02"
    })
    assert conf_res.status_code == 200
    conf_data = conf_res.json()
    assert len(conf_data["conflicts_detected"]) == 1
    conflict_id = conf_data["conflicts_detected"][0]["conflict_id"]

    resolve_res = client.post(
        f"/sync/conflicts/{conflict_id}/resolve",
        headers=headers,
        json={"resolution_action": "resolve_remote", "notes": "Resolved E2E"}
    )
    assert resolve_res.status_code == 200
    assert resolve_res.json()["resolution_status"] == "resolve_remote"

    # 6. Local Backup Export & Restore
    backup_res = client.post("/backup/export", headers=headers, json={"include_audit_logs": True})
    assert backup_res.status_code == 201
    backup_bundle = backup_res.json()
    assert "metadata" in backup_bundle
    assert "checksum" in backup_bundle["metadata"]
    assert "payload" in backup_bundle

    restore_res = client.post("/backup/restore", headers=headers, json=backup_bundle)
    assert restore_res.status_code == 200
    assert restore_res.json()["status"] == "success"

"""Tests for offline local backup export, checksum verification, and restore."""

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
from app.backup.service import create_local_backup, restore_local_backup


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


def test_backup_export_and_restore(client: TestClient, test_db):
    tenant = Tenant(name="Backup Test Lab", code="BKPLAB")
    test_db.add(tenant)
    test_db.flush()

    user = User(
        tenant_id=tenant.id,
        username="backup_admin",
        email="backup@test.com",
        hashed_password=hash_password("Pass1234"),
        full_name="Backup Admin",
    )
    test_db.add(user)
    test_db.commit()

    session = create_session(test_db, tenant_id=tenant.id, user_id=user.id)
    headers = {"Authorization": f"Bearer {session.session_token}"}

    # 1. Export backup via API
    export_res = client.post("/backup/export", headers=headers)
    assert export_res.status_code == 201
    bundle = export_res.json()
    assert "metadata" in bundle
    assert "payload" in bundle
    assert bundle["metadata"]["tenant_id"] == tenant.id
    assert "checksum" in bundle["metadata"]

    # 2. Restore backup via API
    restore_res = client.post("/backup/restore", headers=headers, json=bundle)
    assert restore_res.status_code == 200
    restore_data = restore_res.json()
    assert restore_data["status"] == "success"
    assert restore_data["restored_tenant_id"] == tenant.id


def test_backup_checksum_tamper_detection(test_db):
    tenant = Tenant(name="Tamper Lab", code="TAMPER")
    test_db.add(tenant)
    test_db.commit()

    _, bundle = create_local_backup(test_db, tenant.id)

    # Tamper with payload content
    bundle["payload"]["tenant_name"] = "Hacked Lab Name"

    with pytest.raises(ValueError, match="checksum verification failed"):
        restore_local_backup(test_db, tenant.id, bundle)

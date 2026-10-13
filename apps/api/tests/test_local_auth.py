"""Tests for P09-02 Local Authentication and Session Management."""

from __future__ import annotations

from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base, get_db
import app.models  # noqa: F401
from app.main import app
from app.models.core import Tenant
from app.models.identity import User, SessionRecord
from app.models.audit import AuditLog
from app.security.auth import hash_password, authenticate_user, create_session, revoke_session


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


def test_password_hashing():
    pw = "SecurePass123!"
    hashed = hash_password(pw)
    assert hashed != pw
    from app.security.auth import verify_password
    assert verify_password(pw, hashed) is True
    assert verify_password("WrongPass", hashed) is False


def test_authenticate_user_success_and_failure(test_db: Session):
    tenant = Tenant(name="Apex Diagnostics", code="APEX")
    test_db.add(tenant)
    test_db.flush()

    user = User(
        tenant_id=tenant.id,
        username="dr_apex",
        email="apex@health.test",
        hashed_password=hash_password("CorrectPassword"),
        full_name="Dr. Apex",
    )
    test_db.add(user)
    test_db.commit()

    res = authenticate_user(test_db, tenant_id_or_code="APEX", username="dr_apex", password="CorrectPassword")
    assert res is not None
    u, s = res
    assert u.id == user.id
    assert s.session_token is not None
    assert s.revoked_at is None

    res_fail = authenticate_user(test_db, tenant_id_or_code="APEX", username="dr_apex", password="WrongPassword")
    assert res_fail is None

    res_unknown = authenticate_user(test_db, tenant_id_or_code="UNKNOWN", username="dr_apex", password="CorrectPassword")
    assert res_unknown is None


def test_api_login_and_session_lifecycle(client: TestClient, test_db: Session):
    tenant = Tenant(name="Metro Health", code="METRO")
    test_db.add(tenant)
    test_db.flush()

    user = User(
        tenant_id=tenant.id,
        username="nurse_metro",
        email="nurse@metro.test",
        hashed_password=hash_password("MetroPass123"),
        full_name="Nurse Metro",
    )
    test_db.add(user)
    test_db.commit()

    login_response = client.post(
        "/auth/login",
        json={
            "tenant_id_or_code": "METRO",
            "username": "nurse_metro",
            "password": "MetroPass123",
        },
    )
    assert login_response.status_code == 200
    data = login_response.json()
    assert "access_token" in data
    assert data["username"] == "nurse_metro"
    token = data["access_token"]

    session_response = client.get(
        "/auth/session",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert session_response.status_code == 200
    session_data = session_response.json()
    assert session_data["username"] == "nurse_metro"
    assert session_data["tenant_id"] == tenant.id

    logout_response = client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert logout_response.status_code == 200

    retry_response = client.get(
        "/auth/session",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert retry_response.status_code == 401


def test_audit_logging_on_login(client: TestClient, test_db: Session):
    tenant = Tenant(name="Audit Health", code="AUDIT")
    test_db.add(tenant)
    test_db.flush()

    user = User(
        tenant_id=tenant.id,
        username="auditor",
        email="audit@health.test",
        hashed_password=hash_password("AuditPass123"),
    )
    test_db.add(user)
    test_db.commit()

    client.post(
        "/auth/login",
        json={
            "tenant_id_or_code": "AUDIT",
            "username": "auditor",
            "password": "AuditPass123",
        },
    )

    audit_logs = test_db.scalars(
        select(AuditLog).where(AuditLog.tenant_id == tenant.id)
    ).all()
    assert any(log.action_code == "USER_LOGIN_SUCCESS" for log in audit_logs)


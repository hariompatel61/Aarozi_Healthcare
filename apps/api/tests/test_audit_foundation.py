"""Tests for P02-08 Audit Foundation.

Verifies generic audit log writer and reader, tenant isolation, and bounding.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.models.core import Tenant
from app.models.identity import User
from app.audit.service import log_audit_event, get_audit_logs


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_write_and_read_audit_log(db_session: Session):
    tenant = Tenant(name="Tenant Alpha", code="TA")
    db_session.add(tenant)
    db_session.flush()

    user = User(tenant_id=tenant.id, username="auditor", email="aud@ta.test", hashed_password="pw")
    db_session.add(user)
    db_session.commit()

    entry = log_audit_event(
        db_session,
        tenant_id=tenant.id,
        actor_user_id=user.id,
        action_code="report.release",
        entity_type="report",
        entity_id="rep-1001",
        reason="Physician approval completed",
        before_json={"status": "draft"},
        after_json={"status": "released"},
        correlation_id="corr-abc-123",
    )

    assert entry.id is not None
    assert entry.action_code == "report.release"
    assert entry.reason == "Physician approval completed"
    assert entry.before_json == {"status": "draft"}
    assert entry.after_json == {"status": "released"}

    logs = get_audit_logs(db_session, tenant_id=tenant.id, entity_type="report")
    assert len(logs) == 1
    assert logs[0].id == entry.id
    assert logs[0].correlation_id == "corr-abc-123"


def test_audit_logs_tenant_isolation(db_session: Session):
    t1 = Tenant(name="Tenant One", code="T1")
    t2 = Tenant(name="Tenant Two", code="T2")
    db_session.add_all([t1, t2])
    db_session.commit()

    log_audit_event(db_session, tenant_id=t1.id, action_code="patient.view")
    log_audit_event(db_session, tenant_id=t2.id, action_code="patient.view")

    logs_t1 = get_audit_logs(db_session, tenant_id=t1.id)
    logs_t2 = get_audit_logs(db_session, tenant_id=t2.id)

    assert len(logs_t1) == 1
    assert logs_t1[0].tenant_id == t1.id

    assert len(logs_t2) == 1
    assert logs_t2[0].tenant_id == t2.id


def test_audit_logs_unbounded_limit_clamped(db_session: Session):
    tenant = Tenant(name="Tenant Bulk", code="TB")
    db_session.add(tenant)
    db_session.commit()

    for i in range(120):
        log_audit_event(db_session, tenant_id=tenant.id, action_code=f"action.{i}")

    logs = get_audit_logs(db_session, tenant_id=tenant.id, limit=500)
    assert len(logs) == 100, "Limit must be clamped to max 100 to prevent unbounded queries"

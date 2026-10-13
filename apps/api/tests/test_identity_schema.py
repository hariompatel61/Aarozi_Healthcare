"""Tests for P02-02 Identity Schema.

Verifies User and SessionRecord models, multi-tenancy, and relationships.
"""

from __future__ import annotations

from datetime import datetime, timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.models.core import Tenant
from app.models.identity import User, SessionRecord


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


def test_create_user(db_session: Session):
    tenant = Tenant(name="Acme Health", code="ACME")
    db_session.add(tenant)
    db_session.flush()

    user = User(
        tenant_id=tenant.id,
        username="dr_smith",
        email="smith@acme.test",
        hashed_password="hashed_secret_pw",
        full_name="Dr. Jane Smith",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.tenant_id == tenant.id
    assert user.username == "dr_smith"
    assert user.email == "smith@acme.test"
    assert user.is_active is True
    assert user.is_superuser is False


def test_create_session(db_session: Session):
    tenant = Tenant(name="Acme Health", code="ACME")
    db_session.add(tenant)
    db_session.flush()

    user = User(
        tenant_id=tenant.id,
        username="dr_smith",
        email="smith@acme.test",
        hashed_password="hashed_secret_pw",
    )
    db_session.add(user)
    db_session.flush()

    expires = datetime.utcnow() + timedelta(days=7)
    session_rec = SessionRecord(
        tenant_id=tenant.id,
        user_id=user.id,
        session_token="token_xyz_123",
        user_agent="Mozilla/5.0",
        ip_address="192.168.1.100",
        expires_at=expires,
    )
    db_session.add(session_rec)
    db_session.commit()
    db_session.refresh(session_rec)

    assert session_rec.id is not None
    assert session_rec.user_id == user.id
    assert session_rec.session_token == "token_xyz_123"
    assert session_rec.revoked_at is None
    assert session_rec.user.username == "dr_smith"

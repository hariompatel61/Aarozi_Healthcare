"""Tests for P02-07 Tenant Isolation.

Verifies tenant guards, filtering, boundary enforcement, and cross-tenant isolation.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.models.core import Tenant, Branch
from app.models.identity import User, Role
from app.security.tenant_guard import (
    TenantContext,
    set_tenant_context,
    clear_tenant_context,
    verify_tenant_boundary,
    apply_tenant_filter,
)
from app.errors import ForbiddenError


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
        clear_tenant_context()


def test_tenant_boundary_verification_allows_same_tenant():
    ctx = TenantContext(tenant_id="tenant-1")
    set_tenant_context(ctx)

    # Accessing resource owned by tenant-1 should succeed
    verify_tenant_boundary("tenant-1")


def test_tenant_boundary_verification_blocks_cross_tenant():
    ctx = TenantContext(tenant_id="tenant-1")
    set_tenant_context(ctx)

    # Accessing resource owned by tenant-2 must raise ForbiddenError
    with pytest.raises(ForbiddenError, match="Cross-tenant access forbidden"):
        verify_tenant_boundary("tenant-2")


def test_superuser_bypasses_tenant_boundary():
    ctx = TenantContext(tenant_id="tenant-admin", is_superuser=True)
    set_tenant_context(ctx)

    # Superuser can inspect any tenant
    verify_tenant_boundary("tenant-any")


def test_tenant_filter_isolation_in_database(db_session: Session):
    t1 = Tenant(name="Tenant 1", code="T1")
    t2 = Tenant(name="Tenant 2", code="T2")
    db_session.add_all([t1, t2])
    db_session.flush()

    u1 = User(tenant_id=t1.id, username="alice", email="alice@t1.com", hashed_password="pw")
    u2 = User(tenant_id=t2.id, username="bob", email="bob@t2.com", hashed_password="pw")
    db_session.add_all([u1, u2])
    db_session.commit()

    # Scope context to Tenant 1
    ctx = TenantContext(tenant_id=t1.id, user_id=u1.id)
    set_tenant_context(ctx)

    stmt = select(User)
    filtered_stmt = apply_tenant_filter(stmt, User)
    results = db_session.scalars(filtered_stmt).all()

    assert len(results) == 1
    assert results[0].username == "alice"
    assert results[0].tenant_id == t1.id

    # Switch context to Tenant 2
    ctx2 = TenantContext(tenant_id=t2.id, user_id=u2.id)
    set_tenant_context(ctx2)

    filtered_stmt2 = apply_tenant_filter(stmt, User)
    results2 = db_session.scalars(filtered_stmt2).all()

    assert len(results2) == 1
    assert results2[0].username == "bob"
    assert results2[0].tenant_id == t2.id

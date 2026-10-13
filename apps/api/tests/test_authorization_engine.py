"""Tests for P02-06 Authorization Engine.

Verifies server-side permission resolver and policy checks.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.models.core import Tenant, Branch, Department
from app.models.identity import User, Role, Permission
from app.rbac.service import create_role
from app.rbac.scope import assign_role_to_user
from app.rbac.engine import resolve_user_permissions, authorize_action, enforce_permission
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


def test_resolve_permissions_for_regular_user(db_session: Session):
    tenant = Tenant(name="Tenant One", code="T1")
    db_session.add(tenant)

    p_view = Permission(code="result.view", module="pathology", resource="result", action="view")
    p_enter = Permission(code="result.enter", module="pathology", resource="result", action="enter")
    p_approve = Permission(code="result.approve", module="pathology", resource="result", action="approve", risk_level="critical")
    db_session.add_all([p_view, p_enter, p_approve])
    db_session.commit()

    role = create_role(db_session, tenant_id=tenant.id, name="Technician", permission_ids=[p_view.id, p_enter.id])

    user = User(tenant_id=tenant.id, username="tech_user", email="tech@t1.test", hashed_password="pw")
    db_session.add(user)
    db_session.commit()

    assign_role_to_user(db_session, user_id=user.id, role_id=role.id)

    perms = resolve_user_permissions(db_session, user)
    assert perms == {"result.view", "result.enter"}
    assert "result.approve" not in perms

    assert authorize_action(db_session, user, "result.enter") is True
    assert authorize_action(db_session, user, "result.approve") is False


def test_enforce_permission_raises_forbidden(db_session: Session):
    tenant = Tenant(name="Tenant One", code="T1")
    db_session.add(tenant)
    db_session.flush()

    user = User(tenant_id=tenant.id, username="plain_user", email="plain@t1.test", hashed_password="pw")
    db_session.add(user)
    db_session.commit()

    with pytest.raises(ForbiddenError):
        enforce_permission(db_session, user, "patient.delete")



def test_scope_aware_authorization(db_session: Session):
    tenant = Tenant(name="Tenant One", code="T1")
    branch1 = Branch(tenant=tenant, name="Branch A", code="BA")
    branch2 = Branch(tenant=tenant, name="Branch B", code="BB")
    db_session.add_all([tenant, branch1, branch2])

    p_collect = Permission(code="sample.collect", module="pathology", resource="sample", action="collect")
    db_session.add(p_collect)
    db_session.commit()

    role = create_role(db_session, tenant_id=tenant.id, name="Phlebotomist", permission_ids=[p_collect.id])
    user = User(tenant_id=tenant.id, username="phleb", email="phleb@t1.test", hashed_password="pw")
    db_session.add(user)
    db_session.commit()

    # Scoped only to Branch A
    assign_role_to_user(db_session, user_id=user.id, role_id=role.id, branch_ids=[branch1.id])

    assert authorize_action(db_session, user, "sample.collect", branch_id=branch1.id) is True
    assert authorize_action(db_session, user, "sample.collect", branch_id=branch2.id) is False

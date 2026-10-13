"""Tests for P02-05 User Role Scope.

Verifies branch and department scoping for user roles.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.models.core import Tenant, Branch, Department
from app.models.identity import User, Role
from app.rbac.scope import assign_role_to_user, user_has_branch_access, user_has_department_access
from app.errors import ValidationError


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


def test_assign_role_with_branch_and_department_scope(db_session: Session):
    tenant = Tenant(name="City Diagnostics", code="CD01")
    db_session.add(tenant)
    db_session.flush()

    branch = Branch(tenant_id=tenant.id, name="Downtown Lab", code="DT01")
    db_session.add(branch)
    db_session.flush()

    dept = Department(tenant_id=tenant.id, branch_id=branch.id, name="Biochemistry", code="BIO")
    db_session.add(dept)
    db_session.flush()

    user = User(tenant_id=tenant.id, username="tech1", email="tech1@cd.test", hashed_password="pw")
    role = Role(tenant_id=tenant.id, name="Lab Tech")
    db_session.add_all([user, role])
    db_session.commit()

    user_role = assign_role_to_user(
        db_session,
        user_id=user.id,
        role_id=role.id,
        branch_ids=[branch.id],
        department_ids=[dept.id],
    )

    assert user_role.branch_scope_json == [branch.id]
    assert user_role.department_scope_json == [dept.id]
    assert user_has_branch_access([user_role], branch.id) is True
    assert user_has_branch_access([user_role], "different-branch-id") is False
    assert user_has_department_access([user_role], dept.id) is True
    assert user_has_department_access([user_role], "different-dept-id") is False


def test_cross_tenant_role_assignment_rejected(db_session: Session):
    tenant1 = Tenant(name="Tenant One", code="T1")
    tenant2 = Tenant(name="Tenant Two", code="T2")
    db_session.add_all([tenant1, tenant2])
    db_session.flush()

    user = User(tenant_id=tenant1.id, username="user1", email="u1@test.com", hashed_password="pw")
    role = Role(tenant_id=tenant2.id, name="Cross Role")
    db_session.add_all([user, role])
    db_session.commit()

    with pytest.raises(ValidationError):
        assign_role_to_user(db_session, user_id=user.id, role_id=role.id)

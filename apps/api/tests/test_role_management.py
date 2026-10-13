"""Tests for P02-04 Role Management.

Verifies role CRUD, permission assignment, multi-tenant safety, and system role protection.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.models.core import Tenant
from app.models.identity import Permission
from app.rbac.service import create_role, assign_permissions_to_role, get_roles_by_tenant, delete_role
from app.errors import ConflictError, ValidationError


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


def test_create_and_list_roles(db_session: Session):
    tenant = Tenant(name="Tenant One", code="T1")
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)

    role = create_role(
        db_session,
        tenant_id=tenant.id,
        name="Pathologist",
        description="Can enter and approve test results",
    )
    assert role.id is not None
    assert role.name == "Pathologist"
    assert role.status == "active"

    roles = get_roles_by_tenant(db_session, tenant_id=tenant.id)
    assert len(roles) == 1
    assert roles[0].name == "Pathologist"


def test_duplicate_role_name_in_tenant_fails(db_session: Session):
    tenant = Tenant(name="Tenant One", code="T1")
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)

    create_role(db_session, tenant_id=tenant.id, name="Billing Clerk")
    with pytest.raises(ConflictError):
        create_role(db_session, tenant_id=tenant.id, name="Billing Clerk")


def test_assign_permissions_to_role(db_session: Session):
    tenant = Tenant(name="Tenant One", code="T1")
    db_session.add(tenant)
    p1 = Permission(code="result.enter", module="pathology", resource="result", action="enter")
    p2 = Permission(code="result.approve", module="pathology", resource="result", action="approve", risk_level="critical")
    db_session.add_all([p1, p2])
    db_session.commit()

    role = create_role(
        db_session,
        tenant_id=tenant.id,
        name="Lab Director",
        permission_ids=[p1.id, p2.id],
    )
    assert len(role.role_permissions) == 2
    assigned_codes = {rp.permission.code for rp in role.role_permissions}
    assert assigned_codes == {"result.enter", "result.approve"}


def test_cannot_delete_system_role(db_session: Session):
    tenant = Tenant(name="Tenant One", code="T1")
    db_session.add(tenant)
    db_session.commit()

    role = create_role(db_session, tenant_id=tenant.id, name="Tenant Admin", is_system=True)
    with pytest.raises(ValidationError):
        delete_role(db_session, tenant_id=tenant.id, role_id=role.id)

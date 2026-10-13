"""Tests for P02-01 Core Schema.

Verifies Tenant, Branch, and Department models and their relationships.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.models.core import Tenant, Branch, Department


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


def test_create_tenant(db_session: Session):
    tenant = Tenant(name="Alpha Lab Diagnostics", code="ALPHA")
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)

    assert tenant.id is not None
    assert tenant.name == "Alpha Lab Diagnostics"
    assert tenant.code == "ALPHA"
    assert tenant.is_active is True
    assert tenant.created_at is not None


def test_create_branch_and_department(db_session: Session):
    tenant = Tenant(name="Alpha Lab Diagnostics", code="ALPHA")
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)

    branch = Branch(tenant_id=tenant.id, name="Main Branch", code="MB01")
    db_session.add(branch)
    db_session.commit()
    db_session.refresh(branch)

    assert branch.id is not None
    assert branch.tenant_id == tenant.id
    assert branch.name == "Main Branch"

    dept = Department(tenant_id=tenant.id, branch_id=branch.id, name="Hematology", code="HEM")
    db_session.add(dept)
    db_session.commit()
    db_session.refresh(dept)

    assert dept.id is not None
    assert dept.branch_id == branch.id
    assert dept.name == "Hematology"
    assert dept.code == "HEM"


def test_tenant_relationships(db_session: Session):
    tenant = Tenant(name="Beta Diagnostics", code="BETA")
    db_session.add(tenant)
    db_session.flush()

    branch = Branch(tenant_id=tenant.id, name="City Branch", code="CB01")
    db_session.add(branch)
    db_session.flush()

    dept = Department(tenant_id=tenant.id, branch_id=branch.id, name="Biochemistry", code="BIO")
    db_session.add(dept)
    db_session.commit()
    db_session.refresh(tenant)

    assert len(tenant.branches) == 1
    assert tenant.branches[0].name == "City Branch"
    assert len(tenant.branches[0].departments) == 1
    assert tenant.branches[0].departments[0].name == "Biochemistry"



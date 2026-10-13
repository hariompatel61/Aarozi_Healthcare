"""Tests for P02-03 Permission Catalog.

Verifies the canonical permission catalog, Permission model, and risk levels.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.models.identity import Permission
from app.rbac.permissions import PERMISSIONS_CATALOG, get_all_permissions


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


def test_permission_catalog_completeness():
    perms = get_all_permissions()
    assert len(perms) >= 20

    codes = [p["code"] for p in perms]
    assert len(codes) == len(set(codes)), "Permission codes must be unique"

    required_codes = [
        "patient.view",
        "order.create",
        "sample.collect",
        "result.approve",
        "report.release",
        "billing.create",
        "blood.unit.release",
        "role.manage",
    ]
    for code in required_codes:
        assert code in codes, f"Expected {code} in permission catalog"


def test_permission_catalog_risk_levels():
    perms = get_all_permissions()
    valid_risk_levels = {"normal", "high", "critical"}
    for p in perms:
        assert p["risk_level"] in valid_risk_levels


def test_persist_permissions_in_db(db_session: Session):
    perms = get_all_permissions()
    for p in perms:
        db_perm = Permission(
            code=p["code"],
            module=p["module"],
            resource=p["resource"],
            action=p["action"],
            risk_level=p["risk_level"],
        )
        db_session.add(db_perm)
    db_session.commit()

    count = db_session.query(Permission).count()
    assert count == len(perms)

    approval_perm = db_session.query(Permission).filter_by(code="result.approve").first()
    assert approval_perm is not None
    assert approval_perm.risk_level == "critical"
    assert approval_perm.module == "pathology"
    assert approval_perm.action == "approve"

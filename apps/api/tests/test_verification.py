"""Tests for P05-07: Technician Verification Workflow and RBAC checks."""
import uuid
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.audit.service import get_audit_logs
from app.db import Base
from app.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.core import Branch, Department, Tenant
from app.models.identity import Permission, Role, RolePermission, User, UserRole
from app.models.pathology import Order, OrderItem, Result, ResultValue, Test
from app.models.patient import Patient
from app.pathology.order_workflow import create_order
from app.pathology.result_service import (
    batch_verify_results,
    record_result_values,
    return_result_for_retest,
    verify_result,
)
from app.pathology.test_master import create_test
from app.patient.service import register_patient
from app.security.tenant_guard import TenantContext


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


def _setup_verify_env(db: Session):
    tenant1 = Tenant(name="Alpha Lab", code="AL-01", is_active=True)
    tenant2 = Tenant(name="Beta Lab", code="BL-02", is_active=True)
    db.add_all([tenant1, tenant2])
    db.flush()

    branch1 = Branch(tenant_id=tenant1.id, name="Main Lab", code="ML-01", is_active=True)
    branch2 = Branch(tenant_id=tenant2.id, name="Beta Main", code="BM-01", is_active=True)
    db.add_all([branch1, branch2])
    db.flush()

    dept1 = Department(tenant_id=tenant1.id, branch_id=branch1.id, name="Biochemistry", code="BIO", is_active=True)
    dept2 = Department(tenant_id=tenant2.id, branch_id=branch2.id, name="Biochemistry", code="BIO", is_active=True)
    db.add_all([dept1, dept2])
    db.flush()

    perms = [
        Permission(code="result.view", module="pathology", resource="result", action="view", risk_level="normal"),
        Permission(code="result.enter", module="pathology", resource="result", action="enter", risk_level="normal"),
        Permission(code="result.verify", module="pathology", resource="result", action="verify", risk_level="high"),
        Permission(code="order.create", module="pathology", resource="order", action="create", risk_level="normal"),
        Permission(code="patient.register", module="patient", resource="patient", action="register", risk_level="normal"),
        Permission(code="test.create", module="pathology", resource="test", action="create", risk_level="normal"),
    ]
    db.add_all(perms)
    db.flush()

    # Role 1: Senior Verifier (has result.verify)
    role_verifier = Role(tenant_id=tenant1.id, name="Senior Verifier", is_system=False)
    # Role 2: Junior Tech (has result.enter only, NO result.verify)
    role_junior = Role(tenant_id=tenant1.id, name="Junior Tech", is_system=False)
    db.add_all([role_verifier, role_junior])
    db.flush()

    for p in perms:
        db.add(RolePermission(role_id=role_verifier.id, permission_id=p.id, allow=True))

    for p in perms:
        if p.code != "result.verify":
            db.add(RolePermission(role_id=role_junior.id, permission_id=p.id, allow=True))

    user_verifier = User(tenant_id=tenant1.id, email="verifier@alpha.com", username="sr_verifier", hashed_password="pw")
    user_junior = User(tenant_id=tenant1.id, email="junior@alpha.com", username="jr_tech", hashed_password="pw")
    db.add_all([user_verifier, user_junior])
    db.flush()

    db.add_all([
        UserRole(user_id=user_verifier.id, role_id=role_verifier.id),
        UserRole(user_id=user_junior.id, role_id=role_junior.id),
    ])

    ctx_verifier = TenantContext(tenant_id=tenant1.id, branch_id=branch1.id, user_id=user_verifier.id)
    ctx_junior = TenantContext(tenant_id=tenant1.id, branch_id=branch1.id, user_id=user_junior.id)
    ctx2 = TenantContext(tenant_id=tenant2.id, branch_id=branch2.id, user_id=str(uuid.uuid4()))

    test_hba1c = create_test(
        db,
        tenant_context=ctx_verifier,
        code="HBA1C",
        name="Hemoglobin A1c",
        display_name="HbA1c",
        unit="%",
        department_id=dept1.id,
    )

    pat = register_patient(db, tenant_context=ctx_verifier, first_name="Arthur", last_name="Dent", sex="male")
    order = create_order(db, tenant_context=ctx_verifier, patient_id=pat.id, test_ids=[test_hba1c.id], branch_id=branch1.id)

    db.commit()

    return {
        "ctx_verifier": ctx_verifier,
        "ctx_junior": ctx_junior,
        "ctx2": ctx2,
        "order": order,
        "order_item": order.items[0],
        "test_hba1c": test_hba1c,
    }


def test_verify_result_lifecycle_and_audit(db_session: Session):
    env = _setup_verify_env(db_session)
    ctx_verifier = env["ctx_verifier"]
    ctx_junior = env["ctx_junior"]
    order_item = env["order_item"]

    # 1. Junior enters result (status="entered")
    res = record_result_values(
        db_session,
        tenant_context=ctx_junior,
        order_item_id=order_item.id,
        status="entered",
        values=[{"analyte_code": "HBA1C", "raw_value": "5.6"}],
    )
    assert res.status == "entered"

    # 2. Junior tech cannot verify (ForbiddenError)
    with pytest.raises(ForbiddenError):
        verify_result(db_session, tenant_context=ctx_junior, result_id=res.id)

    # 3. Senior verifier verifies result successfully
    v_res = verify_result(
        db_session,
        tenant_context=ctx_verifier,
        result_id=res.id,
        notes="Calibration and QC within range; verified by Senior Tech",
    )
    assert v_res.status == "verified"
    assert v_res.verified_by == ctx_verifier.user_id
    assert v_res.verified_at is not None

    # Check audit log for verification
    logs = get_audit_logs(db_session, tenant_id=ctx_verifier.tenant_id, entity_type="result", entity_id=res.id)
    assert any(l.action_code == "result.verified" for l in logs)

    # 4. Attempting to re-verify an already verified result raises ConflictError
    with pytest.raises(ConflictError):
        verify_result(db_session, tenant_context=ctx_verifier, result_id=res.id)


def test_return_result_for_retest(db_session: Session):
    env = _setup_verify_env(db_session)
    ctx_verifier = env["ctx_verifier"]
    ctx_junior = env["ctx_junior"]
    order_item = env["order_item"]

    # Enter result
    res = record_result_values(
        db_session,
        tenant_context=ctx_junior,
        order_item_id=order_item.id,
        status="entered",
        values=[{"analyte_code": "HBA1C", "raw_value": "18.5"}],
    )

    # Verifier notices implausibly high value, returns for retest
    returned = return_result_for_retest(
        db_session,
        tenant_context=ctx_verifier,
        result_id=res.id,
        reason="Suspicion of analytical interference / pipetting artifact; please re-run sample",
    )
    assert returned.status == "draft"
    assert returned.verified_by is None
    assert "Suspicion of analytical interference" in returned.notes

    # Verify audit event
    logs = get_audit_logs(db_session, tenant_id=ctx_verifier.tenant_id, entity_type="result", entity_id=res.id)
    assert any(l.action_code == "result.returned_for_retest" for l in logs)


def test_batch_verify_and_tenant_isolation(db_session: Session):
    env = _setup_verify_env(db_session)
    ctx_verifier = env["ctx_verifier"]
    ctx2 = env["ctx2"]
    order_item = env["order_item"]

    res = record_result_values(
        db_session,
        tenant_context=ctx_verifier,
        order_item_id=order_item.id,
        status="entered",
        values=[{"analyte_code": "HBA1C", "raw_value": "5.4"}],
    )

    # Tenant 2 cannot verify Tenant 1 result
    with pytest.raises(NotFoundError):
        verify_result(db_session, tenant_context=ctx2, result_id=res.id)

    # Batch verification
    batch_res = batch_verify_results(
        db_session,
        tenant_context=ctx_verifier,
        result_ids=[res.id],
        notes="Batch release of morning OPD run",
    )
    assert len(batch_res) == 1
    assert batch_res[0].status == "verified"


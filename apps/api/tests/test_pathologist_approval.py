"""Tests for P05-08: Pathologist Approval, Digital Signing, Release Controls, and Auditability."""
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
    approve_and_release_result,
    batch_approve_results,
    record_result_values,
    reject_pathologist_approval,
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


def _setup_pathologist_env(db: Session):
    tenant1 = Tenant(name="Premier Pathology", code="PP-01", is_active=True)
    tenant2 = Tenant(name="Global Labs", code="GL-02", is_active=True)
    db.add_all([tenant1, tenant2])
    db.flush()

    branch1 = Branch(tenant_id=tenant1.id, name="City Central", code="CC-01", is_active=True)
    branch2 = Branch(tenant_id=tenant2.id, name="Global Lab", code="GL-01", is_active=True)
    db.add_all([branch1, branch2])
    db.flush()

    dept1 = Department(tenant_id=tenant1.id, branch_id=branch1.id, name="Clinical Chemistry", code="CC", is_active=True)
    dept2 = Department(tenant_id=tenant2.id, branch_id=branch2.id, name="Clinical Chemistry", code="CC", is_active=True)
    db.add_all([dept1, dept2])
    db.flush()

    perms = [
        Permission(code="result.view", module="pathology", resource="result", action="view", risk_level="normal"),
        Permission(code="result.enter", module="pathology", resource="result", action="enter", risk_level="normal"),
        Permission(code="result.verify", module="pathology", resource="result", action="verify", risk_level="high"),
        Permission(code="result.approve", module="pathology", resource="result", action="approve", risk_level="critical"),
        Permission(code="order.create", module="pathology", resource="order", action="create", risk_level="normal"),
        Permission(code="patient.register", module="patient", resource="patient", action="register", risk_level="normal"),
        Permission(code="test.create", module="pathology", resource="test", action="create", risk_level="normal"),
    ]
    db.add_all(perms)
    db.flush()

    # Roles
    role_pathologist = Role(tenant_id=tenant1.id, name="Chief Pathologist", is_system=False)
    role_tech = Role(tenant_id=tenant1.id, name="Bench Tech", is_system=False)
    db.add_all([role_pathologist, role_tech])
    db.flush()

    for p in perms:
        db.add(RolePermission(role_id=role_pathologist.id, permission_id=p.id, allow=True))

    for p in perms:
        if p.code != "result.approve":
            db.add(RolePermission(role_id=role_tech.id, permission_id=p.id, allow=True))

    user_pathologist = User(tenant_id=tenant1.id, email="path@premier.com", username="dr_pathologist", hashed_password="pw")
    user_tech = User(tenant_id=tenant1.id, email="tech@premier.com", username="tech_user", hashed_password="pw")
    db.add_all([user_pathologist, user_tech])
    db.flush()

    db.add_all([
        UserRole(user_id=user_pathologist.id, role_id=role_pathologist.id),
        UserRole(user_id=user_tech.id, role_id=role_tech.id),
    ])

    ctx_pathologist = TenantContext(tenant_id=tenant1.id, branch_id=branch1.id, user_id=user_pathologist.id)
    ctx_tech = TenantContext(tenant_id=tenant1.id, branch_id=branch1.id, user_id=user_tech.id)
    ctx2 = TenantContext(tenant_id=tenant2.id, branch_id=branch2.id, user_id=str(uuid.uuid4()))

    test_lipid = create_test(
        db,
        tenant_context=ctx_pathologist,
        code="CHOL",
        name="Total Cholesterol",
        display_name="Cholesterol",
        unit="mg/dL",
        department_id=dept1.id,
    )

    pat = register_patient(db, tenant_context=ctx_pathologist, first_name="Thomas", last_name="Edison", sex="male")
    order = create_order(db, tenant_context=ctx_pathologist, patient_id=pat.id, test_ids=[test_lipid.id], branch_id=branch1.id)

    db.commit()

    return {
        "ctx_pathologist": ctx_pathologist,
        "ctx_tech": ctx_tech,
        "ctx2": ctx2,
        "order": order,
        "order_item": order.items[0],
        "test_lipid": test_lipid,
    }


def test_pathologist_approval_and_digital_signing(db_session: Session):
    env = _setup_pathologist_env(db_session)
    ctx_path = env["ctx_pathologist"]
    ctx_tech = env["ctx_tech"]
    order_item = env["order_item"]

    # 1. Tech enters and verifies
    res = record_result_values(
        db_session,
        tenant_context=ctx_tech,
        order_item_id=order_item.id,
        status="entered",
        values=[{"analyte_code": "CHOL", "raw_value": "185.0"}],
    )
    res_verified = verify_result(db_session, tenant_context=ctx_tech, result_id=res.id)
    assert res_verified.status == "verified"

    # 2. Bench tech cannot approve (ForbiddenError)
    with pytest.raises(ForbiddenError):
        approve_and_release_result(db_session, tenant_context=ctx_tech, result_id=res.id)

    # 3. Pathologist approves and signs release
    res_approved = approve_and_release_result(
        db_session,
        tenant_context=ctx_path,
        result_id=res.id,
        notes="Reviewed and clinically correlated; report released",
    )
    assert res_approved.status == "released"
    assert res_approved.approved_by == ctx_path.user_id
    assert res_approved.approved_at is not None
    assert res_approved.signature_hash is not None
    assert len(res_approved.signature_hash) == 64  # SHA256 length

    # OrderItem marked completed
    db_session.refresh(order_item)
    assert order_item.status == "completed"

    # Audit event verification
    logs = get_audit_logs(db_session, tenant_id=ctx_path.tenant_id, entity_type="result", entity_id=res.id)
    assert any(l.action_code == "result.approved" for l in logs)

    # Re-approving released result raises ConflictError
    with pytest.raises(ConflictError):
        approve_and_release_result(db_session, tenant_context=ctx_path, result_id=res.id)


def test_reject_pathologist_approval(db_session: Session):
    env = _setup_pathologist_env(db_session)
    ctx_path = env["ctx_pathologist"]
    ctx_tech = env["ctx_tech"]
    order_item = env["order_item"]

    res = record_result_values(
        db_session,
        tenant_context=ctx_tech,
        order_item_id=order_item.id,
        status="entered",
        values=[{"analyte_code": "CHOL", "raw_value": "395.0"}],
    )
    verify_result(db_session, tenant_context=ctx_tech, result_id=res.id)

    # Pathologist rejects approval back to entered for re-check
    with pytest.raises(ValidationError):
        reject_pathologist_approval(db_session, tenant_context=ctx_path, result_id=res.id, reason="")

    rejected = reject_pathologist_approval(
        db_session,
        tenant_context=ctx_path,
        result_id=res.id,
        reason="Please check sample for lipemia and re-evaluate on dilution",
    )
    assert rejected.status == "entered"
    assert rejected.verified_by is None
    assert "lipemia" in rejected.notes

    # Audit event verification
    logs = get_audit_logs(db_session, tenant_id=ctx_path.tenant_id, entity_type="result", entity_id=res.id)
    assert any(l.action_code == "result.approval_rejected" for l in logs)


def test_batch_approval_and_tenant_isolation(db_session: Session):
    env = _setup_pathologist_env(db_session)
    ctx_path = env["ctx_pathologist"]
    ctx2 = env["ctx2"]
    order_item = env["order_item"]

    res = record_result_values(
        db_session,
        tenant_context=ctx_path,
        order_item_id=order_item.id,
        status="entered",
        values=[{"analyte_code": "CHOL", "raw_value": "170.0"}],
    )
    verify_result(db_session, tenant_context=ctx_path, result_id=res.id)

    # Tenant 2 cannot approve Tenant 1 result
    with pytest.raises(NotFoundError):
        approve_and_release_result(db_session, tenant_context=ctx2, result_id=res.id)

    # Batch approval
    batch_approved = batch_approve_results(
        db_session,
        tenant_context=ctx_path,
        result_ids=[res.id],
        notes="Batch morning OPD release",
    )
    assert len(batch_approved) == 1
    assert batch_approved[0].status == "released"


"""Tests for P05-09: Result Amendment Versioning, Immutability, Audit, and RBAC."""
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
    amend_result,
    approve_and_release_result,
    get_result_version_history,
    record_result_values,
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


def _setup_amendment_env(db: Session):
    tenant1 = Tenant(name="Metro Pathology", code="MP-01", is_active=True)
    tenant2 = Tenant(name="Global Labs", code="GL-02", is_active=True)
    db.add_all([tenant1, tenant2])
    db.flush()

    branch1 = Branch(tenant_id=tenant1.id, name="City Central", code="CC-01", is_active=True)
    branch2 = Branch(tenant_id=tenant2.id, name="Global Lab", code="GL-01", is_active=True)
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
        Permission(code="result.edit", module="pathology", resource="result", action="edit", risk_level="high"),
        Permission(code="result.approve", module="pathology", resource="result", action="approve", risk_level="critical"),
        Permission(code="order.create", module="pathology", resource="order", action="create", risk_level="normal"),
        Permission(code="patient.register", module="patient", resource="patient", action="register", risk_level="normal"),
        Permission(code="test.create", module="pathology", resource="test", action="create", risk_level="normal"),
    ]
    db.add_all(perms)
    db.flush()

    # Roles
    role_pathologist = Role(tenant_id=tenant1.id, name="Pathologist", is_system=False)
    role_readonly = Role(tenant_id=tenant1.id, name="ReadOnly", is_system=False)
    db.add_all([role_pathologist, role_readonly])
    db.flush()

    for p in perms:
        db.add(RolePermission(role_id=role_pathologist.id, permission_id=p.id, allow=True))
    p_view = next(p for p in perms if p.code == "result.view")
    db.add(RolePermission(role_id=role_readonly.id, permission_id=p_view.id, allow=True))

    user_pathologist = User(tenant_id=tenant1.id, email="doc@metro.com", username="dr_metro", hashed_password="pw")
    user_ro = User(tenant_id=tenant1.id, email="ro@metro.com", username="ro_metro", hashed_password="pw")
    db.add_all([user_pathologist, user_ro])
    db.flush()

    db.add_all([
        UserRole(user_id=user_pathologist.id, role_id=role_pathologist.id),
        UserRole(user_id=user_ro.id, role_id=role_readonly.id),
    ])

    ctx_doc = TenantContext(tenant_id=tenant1.id, branch_id=branch1.id, user_id=user_pathologist.id)
    ctx_ro = TenantContext(tenant_id=tenant1.id, branch_id=branch1.id, user_id=user_ro.id)
    ctx2 = TenantContext(tenant_id=tenant2.id, branch_id=branch2.id, user_id=str(uuid.uuid4()))

    test_hba1c = create_test(
        db,
        tenant_context=ctx_doc,
        code="HBA1C",
        name="Hemoglobin A1c",
        display_name="HbA1c",
        unit="%",
        department_id=dept1.id,
    )

    pat = register_patient(db, tenant_context=ctx_doc, first_name="Alan", last_name="Turing", sex="male")
    order = create_order(db, tenant_context=ctx_doc, patient_id=pat.id, test_ids=[test_hba1c.id], branch_id=branch1.id)

    db.commit()

    return {
        "ctx_doc": ctx_doc,
        "ctx_ro": ctx_ro,
        "ctx2": ctx2,
        "order": order,
        "order_item": order.items[0],
        "test_hba1c": test_hba1c,
    }


def test_result_amendment_lifecycle_and_audit(db_session: Session):
    env = _setup_amendment_env(db_session)
    ctx_doc = env["ctx_doc"]
    ctx_ro = env["ctx_ro"]
    order_item = env["order_item"]

    # 1. Enter, verify, and release version 1 (HbA1c = 5.7%)
    res_v1 = record_result_values(
        db_session,
        tenant_context=ctx_doc,
        order_item_id=order_item.id,
        status="entered",
        values=[{"analyte_code": "HBA1C", "raw_value": "5.7"}],
    )
    verify_result(db_session, tenant_context=ctx_doc, result_id=res_v1.id)
    approve_and_release_result(db_session, tenant_context=ctx_doc, result_id=res_v1.id)
    assert res_v1.status == "released"
    assert res_v1.version == 1

    # 2. Validation: Empty amendment reason rejected
    with pytest.raises(ValidationError):
        amend_result(
            db_session,
            tenant_context=ctx_doc,
            result_id=res_v1.id,
            amendment_reason="   ",
            updated_values=[{"analyte_code": "HBA1C", "raw_value": "5.9"}],
        )

    # 3. RBAC: Read-only user cannot amend (ForbiddenError)
    with pytest.raises(ForbiddenError):
        amend_result(
            db_session,
            tenant_context=ctx_ro,
            result_id=res_v1.id,
            amendment_reason="Clerical correction",
            updated_values=[{"analyte_code": "HBA1C", "raw_value": "5.9"}],
        )

    # 4. Pathologist amends result
    res_v2 = amend_result(
        db_session,
        tenant_context=ctx_doc,
        result_id=res_v1.id,
        amendment_reason="Corrected transcription from manual HPLC logbook following secondary bench review",
        updated_values=[{"analyte_code": "HBA1C", "raw_value": "5.9"}],
    )

    # Verify Version 1 state (must be immutable and marked 'amended')
    db_session.refresh(res_v1)
    assert res_v1.status == "amended"
    assert res_v1.version == 1
    assert float(res_v1.values[0].numeric_value) == 5.7
    assert "transcription" in res_v1.amendment_reason

    # Verify Version 2 state
    assert res_v2.id != res_v1.id
    assert res_v2.status == "entered"
    assert res_v2.version == 2
    assert res_v2.amended_from_id == res_v1.id
    assert float(res_v2.values[0].numeric_value) == 5.9

    # Verify audit event
    logs = get_audit_logs(db_session, tenant_id=ctx_doc.tenant_id, entity_type="result", entity_id=res_v2.id)
    assert any(l.action_code == "result.amended" for l in logs)

    # 5. Version History returns both versions in order
    history = get_result_version_history(db_session, tenant_context=ctx_doc, order_item_id=order_item.id)
    assert len(history) == 2
    assert history[0].version == 1
    assert history[0].status == "amended"
    assert history[1].version == 2
    assert history[1].status == "entered"


def test_cannot_amend_unreleased_result(db_session: Session):
    env = _setup_amendment_env(db_session)
    ctx_doc = env["ctx_doc"]
    order_item = env["order_item"]

    # Result in entered status
    res = record_result_values(
        db_session,
        tenant_context=ctx_doc,
        order_item_id=order_item.id,
        status="entered",
        values=[{"analyte_code": "HBA1C", "raw_value": "6.0"}],
    )

    # Amending non-released result raises ConflictError
    with pytest.raises(ConflictError):
        amend_result(
            db_session,
            tenant_context=ctx_doc,
            result_id=res.id,
            amendment_reason="Premature amendment attempt",
        )


def test_tenant_isolation_on_amendments(db_session: Session):
    env = _setup_amendment_env(db_session)
    ctx_doc = env["ctx_doc"]
    ctx2 = env["ctx2"]
    order_item = env["order_item"]

    res = record_result_values(
        db_session,
        tenant_context=ctx_doc,
        order_item_id=order_item.id,
        status="entered",
        values=[{"analyte_code": "HBA1C", "raw_value": "5.5"}],
    )
    verify_result(db_session, tenant_context=ctx_doc, result_id=res.id)
    approve_and_release_result(db_session, tenant_context=ctx_doc, result_id=res.id)

    # Tenant 2 cannot access or amend
    with pytest.raises(NotFoundError):
        amend_result(
            db_session,
            tenant_context=ctx2,
            result_id=res.id,
            amendment_reason="Cross-tenant amendment",
        )

    t2_history = get_result_version_history(db_session, tenant_context=ctx2, order_item_id=order_item.id)
    assert len(t2_history) == 0


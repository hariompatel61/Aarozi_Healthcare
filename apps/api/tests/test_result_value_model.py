"""Tests for P05-02: Structured Result Values, Analyte Entry, Flagging, and Auditability."""
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.audit.service import get_audit_logs
from app.db import Base
from app.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.core import Branch, Department, Tenant
from app.models.identity import Permission, Role, RolePermission, User, UserRole
from app.models.pathology import Order, OrderItem, Result, ResultValue, Test, TestReferenceRange
from app.models.patient import Patient
from app.pathology.order_workflow import create_order
from app.pathology.reference_range_service import add_reference_range
from app.pathology.result_service import (
    get_result,
    list_results,
    record_result_values,
    update_result_value,
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


def _setup_result_env(db: Session):
    tenant1 = Tenant(name="Metro Labs", code="ML-01", is_active=True)
    tenant2 = Tenant(name="Apex Labs", code="AL-02", is_active=True)
    db.add_all([tenant1, tenant2])
    db.flush()

    branch1 = Branch(tenant_id=tenant1.id, name="Main Branch", code="MB-01", is_active=True)
    branch2 = Branch(tenant_id=tenant2.id, name="Apex Branch", code="AB-01", is_active=True)
    db.add_all([branch1, branch2])
    db.flush()

    dept1 = Department(tenant_id=tenant1.id, branch_id=branch1.id, name="Biochemistry", code="BIO", is_active=True)
    dept2 = Department(tenant_id=tenant2.id, branch_id=branch2.id, name="Biochemistry", code="BIO", is_active=True)
    db.add_all([dept1, dept2])
    db.flush()

    # Permissions
    perms = [
        Permission(code="result.view", module="pathology", resource="result", action="view", risk_level="normal"),
        Permission(code="result.enter", module="pathology", resource="result", action="enter", risk_level="normal"),
        Permission(code="result.edit", module="pathology", resource="result", action="edit", risk_level="high"),
        Permission(code="order.create", module="pathology", resource="order", action="create", risk_level="normal"),
        Permission(code="patient.register", module="patient", resource="patient", action="register", risk_level="normal"),
        Permission(code="test.create", module="pathology", resource="test", action="create", risk_level="normal"),
    ]
    db.add_all(perms)
    db.flush()

    # Roles
    role_tech = Role(tenant_id=tenant1.id, name="Technician", is_system=False)
    role_viewer = Role(tenant_id=tenant1.id, name="Viewer", is_system=False)
    db.add_all([role_tech, role_viewer])
    db.flush()

    for p in perms:
        db.add(RolePermission(role_id=role_tech.id, permission_id=p.id, allow=True))
    perm_view = next(p for p in perms if p.code == "result.view")
    db.add(RolePermission(role_id=role_viewer.id, permission_id=perm_view.id, allow=True))

    user_tech = User(tenant_id=tenant1.id, email="tech@metro.com", username="tech_user", hashed_password="pw")
    user_viewer = User(tenant_id=tenant1.id, email="view@metro.com", username="view_user", hashed_password="pw")
    db.add_all([user_tech, user_viewer])
    db.flush()

    db.add_all([
        UserRole(user_id=user_tech.id, role_id=role_tech.id),
        UserRole(user_id=user_viewer.id, role_id=role_viewer.id),
    ])

    ctx1_tech = TenantContext(tenant_id=tenant1.id, branch_id=branch1.id, user_id=user_tech.id)
    ctx1_viewer = TenantContext(tenant_id=tenant1.id, branch_id=branch1.id, user_id=user_viewer.id)
    ctx2 = TenantContext(tenant_id=tenant2.id, branch_id=branch2.id, user_id=str(uuid.uuid4()))

    # Test with Reference Ranges
    test_glu = create_test(
        db,
        tenant_context=ctx1_tech,
        code="GLU_FAST",
        name="Glucose Fasting",
        display_name="Glucose",
        unit="mg/dL",
        department_id=dept1.id,
    )
    add_reference_range(
        db,
        tenant_context=ctx1_tech,
        test_id=test_glu.id,
        sex="all",
        age_min=18,
        age_max=120,
        context="fasting",
        low_value=70.0,
        high_value=99.0,
        critical_low=45.0,
        critical_high=400.0,
        text_range="70.0 - 99.0 mg/dL",
    )

    # Patient
    pat1 = register_patient(
        db,
        tenant_context=ctx1_tech,
        first_name="Albert",
        last_name="Einstein",
        sex="male",
        date_of_birth=date(1980, 5, 20),
    )

    # Order
    order1 = create_order(
        db,
        tenant_context=ctx1_tech,
        patient_id=pat1.id,
        test_ids=[test_glu.id],
        branch_id=branch1.id,
    )

    db.commit()

    return {
        "tenant1": tenant1,
        "tenant2": tenant2,
        "ctx1_tech": ctx1_tech,
        "ctx1_viewer": ctx1_viewer,
        "ctx2": ctx2,
        "test_glu": test_glu,
        "patient1": pat1,
        "order1": order1,
        "order_item1": order1.items[0],
    }


def test_record_result_values_and_automatic_flagging(db_session: Session):
    env = _setup_result_env(db_session)
    ctx = env["ctx1_tech"]
    order_item = env["order_item1"]

    # 1. Enter abnormal high value (145.0 mg/dL against 70-99)
    result = record_result_values(
        db_session,
        tenant_context=ctx,
        order_item_id=order_item.id,
        context="fasting",
        status="entered",
        values=[
            {
                "analyte_code": "GLU_FAST",
                "raw_value": "145.0",
                "notes": "Sample received without hemolysis",
            }
        ],
    )

    assert result.id is not None
    assert result.status == "entered"
    assert result.entered_by == ctx.user_id
    assert result.entered_at is not None
    assert len(result.values) == 1

    rv = result.values[0]
    assert rv.analyte_code == "GLU_FAST"
    assert float(rv.numeric_value) == 145.0
    assert rv.unit == "mg/dL"
    assert rv.abnormal_flag == "high"
    assert not rv.critical_flag
    assert rv.reference_text == "70.0 - 99.0 mg/dL"

    # Audit log check
    logs = get_audit_logs(db_session, tenant_id=ctx.tenant_id, entity_type="result", entity_id=result.id)
    assert any(l.action_code == "result.entered" for l in logs)


def test_critical_panic_flag_and_update_value(db_session: Session):
    env = _setup_result_env(db_session)
    ctx = env["ctx1_tech"]
    order_item = env["order_item1"]

    # Enter critical low value (35.0 mg/dL against critical_low=45.0)
    result = record_result_values(
        db_session,
        tenant_context=ctx,
        order_item_id=order_item.id,
        context="fasting",
        status="draft",
        values=[
            {
                "analyte_code": "GLU_FAST",
                "raw_value": "35.0",
            }
        ],
    )
    rv = result.values[0]
    assert rv.abnormal_flag == "critical_low"
    assert rv.critical_flag is True

    # Update value to normal (85.0 mg/dL)
    updated_rv = update_result_value(
        db_session,
        tenant_context=ctx,
        result_value_id=rv.id,
        raw_value="85.0",
        notes="Re-run on secondary analyzer confirmed normal",
    )
    assert float(updated_rv.numeric_value) == 85.0
    assert updated_rv.abnormal_flag == "normal"
    assert updated_rv.critical_flag is False

    # Check update audit log
    logs = get_audit_logs(db_session, tenant_id=ctx.tenant_id, entity_type="result_value", entity_id=rv.id)
    assert any(l.action_code == "result_value.updated" for l in logs)



def test_rbac_and_tenant_isolation(db_session: Session):
    env = _setup_result_env(db_session)
    ctx_tech = env["ctx1_tech"]
    ctx_viewer = env["ctx1_viewer"]
    ctx2 = env["ctx2"]
    order_item = env["order_item1"]

    # 1. Tech enters result
    res = record_result_values(
        db_session,
        tenant_context=ctx_tech,
        order_item_id=order_item.id,
        context="fasting",
        status="entered",
        values=[{"analyte_code": "GLU_FAST", "raw_value": "90.0"}],
    )

    # 2. Viewer can view result
    view_res = get_result(db_session, tenant_context=ctx_viewer, result_id=res.id)
    assert view_res.id == res.id

    items, count = list_results(db_session, tenant_context=ctx_viewer, order_item_id=order_item.id)
    assert count == 1
    assert len(items) == 1

    # 3. Viewer cannot enter or edit values
    with pytest.raises(ForbiddenError):
        record_result_values(
            db_session,
            tenant_context=ctx_viewer,
            order_item_id=order_item.id,
            values=[{"analyte_code": "GLU_FAST", "raw_value": "95.0"}],
        )

    with pytest.raises(ForbiddenError):
        update_result_value(
            db_session,
            tenant_context=ctx_viewer,
            result_value_id=res.values[0].id,
            raw_value="95.0",
        )

    # 4. Multi-tenant isolation: Tenant 2 cannot see or edit Tenant 1 results
    with pytest.raises(NotFoundError):
        get_result(db_session, tenant_context=ctx2, result_id=res.id)

    with pytest.raises(NotFoundError):
        update_result_value(
            db_session,
            tenant_context=ctx2,
            result_value_id=res.values[0].id,
            raw_value="95.0",
        )

    t2_items, t2_count = list_results(db_session, tenant_context=ctx2)
    assert t2_count == 0
    assert len(t2_items) == 0


def test_conflict_on_editing_released_result(db_session: Session):
    env = _setup_result_env(db_session)
    ctx = env["ctx1_tech"]
    order_item = env["order_item1"]

    res = record_result_values(
        db_session,
        tenant_context=ctx,
        order_item_id=order_item.id,
        status="entered",
        values=[{"analyte_code": "GLU_FAST", "raw_value": "90.0"}],
    )

    # Manually transition to released for test
    res.status = "released"
    db_session.commit()

    # Direct edit of released result value is forbidden
    with pytest.raises(ConflictError):
        update_result_value(
            db_session,
            tenant_context=ctx,
            result_value_id=res.values[0].id,
            raw_value="95.0",
        )


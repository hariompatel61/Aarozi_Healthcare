"""Tests for P05-05: Department/Test Worklists with Pagination, Filters, and RBAC."""
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.errors import ForbiddenError, NotFoundError
from app.models.core import Branch, Department, Tenant
from app.models.identity import Permission, Role, RolePermission, User, UserRole
from app.models.pathology import Order, OrderItem, Result, ResultValue, Sample, Test
from app.models.patient import Patient
from app.pathology.order_workflow import create_order
from app.pathology.reference_range_service import add_reference_range
from app.pathology.result_service import record_result_values
from app.pathology.sample_workflow import create_sample_for_order_item, collect_sample
from app.pathology.test_master import create_test
from app.pathology.worklist_service import get_department_worklist, get_worklist_summary
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


def _setup_worklist_env(db: Session):
    tenant1 = Tenant(name="Central Diagnostics", code="CD-01", is_active=True)
    tenant2 = Tenant(name="Apex Diagnostic", code="AD-02", is_active=True)
    db.add_all([tenant1, tenant2])
    db.flush()

    branch1 = Branch(tenant_id=tenant1.id, name="Downtown Branch", code="DT-01", is_active=True)
    branch2 = Branch(tenant_id=tenant2.id, name="Apex Branch", code="AP-01", is_active=True)
    db.add_all([branch1, branch2])
    db.flush()

    dept_hem = Department(tenant_id=tenant1.id, branch_id=branch1.id, name="Hematology", code="HEM", is_active=True)
    dept_bio = Department(tenant_id=tenant1.id, branch_id=branch1.id, name="Biochemistry", code="BIO", is_active=True)
    db.add_all([dept_hem, dept_bio])
    db.flush()

    perms = [
        Permission(code="result.view", module="pathology", resource="result", action="view", risk_level="normal"),
        Permission(code="result.enter", module="pathology", resource="result", action="enter", risk_level="normal"),
        Permission(code="sample.view", module="pathology", resource="sample", action="view", risk_level="normal"),
        Permission(code="sample.collect", module="pathology", resource="sample", action="collect", risk_level="normal"),
        Permission(code="order.create", module="pathology", resource="order", action="create", risk_level="normal"),
        Permission(code="patient.register", module="patient", resource="patient", action="register", risk_level="normal"),
        Permission(code="test.create", module="pathology", resource="test", action="create", risk_level="normal"),
    ]
    db.add_all(perms)
    db.flush()

    role_tech = Role(tenant_id=tenant1.id, name="Technician", is_system=False)
    role_unauth = Role(tenant_id=tenant1.id, name="Unauth", is_system=False)
    db.add_all([role_tech, role_unauth])
    db.flush()

    for p in perms:
        db.add(RolePermission(role_id=role_tech.id, permission_id=p.id, allow=True))

    user_tech = User(tenant_id=tenant1.id, email="tech@central.com", username="tech_c", hashed_password="pw")
    user_unauth = User(tenant_id=tenant1.id, email="unauth@central.com", username="unauth_c", hashed_password="pw")
    db.add_all([user_tech, user_unauth])
    db.flush()

    db.add_all([
        UserRole(user_id=user_tech.id, role_id=role_tech.id),
        UserRole(user_id=user_unauth.id, role_id=role_unauth.id),
    ])

    ctx1 = TenantContext(tenant_id=tenant1.id, branch_id=branch1.id, user_id=user_tech.id)
    ctx1_unauth = TenantContext(tenant_id=tenant1.id, branch_id=branch1.id, user_id=user_unauth.id)
    ctx2 = TenantContext(tenant_id=tenant2.id, branch_id=branch2.id, user_id=str(uuid.uuid4()))

    # Tests
    test_cbc = create_test(
        db,
        tenant_context=ctx1,
        code="CBC",
        name="Complete Blood Count",
        display_name="CBC",
        department_id=dept_hem.id,
    )
    test_glu = create_test(
        db,
        tenant_context=ctx1,
        code="GLU",
        name="Blood Glucose",
        display_name="Glucose",
        unit="mg/dL",
        department_id=dept_bio.id,
    )
    add_reference_range(
        db,
        tenant_context=ctx1,
        test_id=test_glu.id,
        sex="all",
        low_value=70.0,
        high_value=100.0,
        critical_low=40.0,
        critical_high=400.0,
        text_range="70 - 100 mg/dL",
    )

    # Patients
    pat1 = register_patient(db, tenant_context=ctx1, first_name="Clark", last_name="Kent", sex="male")
    pat2 = register_patient(db, tenant_context=ctx1, first_name="Bruce", last_name="Wayne", sex="male")

    # Order 1 (Clark Kent): CBC and Glucose
    order1 = create_order(db, tenant_context=ctx1, patient_id=pat1.id, test_ids=[test_cbc.id, test_glu.id], branch_id=branch1.id)

    # Order 2 (Bruce Wayne): CBC only
    order2 = create_order(db, tenant_context=ctx1, patient_id=pat2.id, test_ids=[test_cbc.id], branch_id=branch1.id)

    db.commit()

    return {
        "tenant1": tenant1,
        "tenant2": tenant2,
        "ctx1": ctx1,
        "ctx1_unauth": ctx1_unauth,
        "ctx2": ctx2,
        "dept_hem": dept_hem,
        "dept_bio": dept_bio,
        "test_cbc": test_cbc,
        "test_glu": test_glu,
        "order1": order1,
        "order2": order2,
        "pat1": pat1,
        "pat2": pat2,
    }


def test_worklist_filtering_by_department_and_status(db_session: Session):
    env = _setup_worklist_env(db_session)
    ctx = env["ctx1"]

    # Total order items in tenant 1 = 3 (order1 has 2, order2 has 1)
    items_all, count_all = get_department_worklist(db_session, tenant_context=ctx)
    assert count_all == 3
    assert len(items_all) == 3

    # Filter by Biochemistry: only 1 item (Glucose)
    items_bio, count_bio = get_department_worklist(
        db_session,
        tenant_context=ctx,
        department_id=env["dept_bio"].id,
    )
    assert count_bio == 1
    assert items_bio[0]["test_code"] == "GLU"

    # Filter by Hematology: 2 items (CBC for Kent, CBC for Wayne)
    items_hem, count_hem = get_department_worklist(
        db_session,
        tenant_context=ctx,
        department_id=env["dept_hem"].id,
    )
    assert count_hem == 2
    assert all(it["test_code"] == "CBC" for it in items_hem)

    # Initial status of all items is "pending_entry"
    items_pending, count_pending = get_department_worklist(
        db_session,
        tenant_context=ctx,
        status="pending_entry",
    )
    assert count_pending == 3

    # Enter result for Glucose
    glu_item = next(it for it in env["order1"].items if it.test_id == env["test_glu"].id)
    record_result_values(
        db_session,
        tenant_context=ctx,
        order_item_id=glu_item.id,
        status="entered",
        values=[{"analyte_code": "GLU", "raw_value": "88.0"}],
    )

    # Now pending_entry should be 2, and pending_verification should be 1
    items_pe_after, count_pe_after = get_department_worklist(db_session, tenant_context=ctx, status="pending_entry")
    assert count_pe_after == 2

    items_pv, count_pv = get_department_worklist(db_session, tenant_context=ctx, status="pending_verification")
    assert count_pv == 1
    assert items_pv[0]["test_code"] == "GLU"
    assert items_pv[0]["result_status"] == "entered"


def test_worklist_search_critical_flag_and_summary(db_session: Session):
    env = _setup_worklist_env(db_session)
    ctx = env["ctx1"]

    # 1. Search by patient name
    items_wayne, count_wayne = get_department_worklist(db_session, tenant_context=ctx, search="Wayne")
    assert count_wayne == 1
    assert "Wayne" in items_wayne[0]["patient_name"]

    # 2. Enter panic critical value on Glucose (450 mg/dL > critical_high 400)
    glu_item = next(it for it in env["order1"].items if it.test_id == env["test_glu"].id)
    record_result_values(
        db_session,
        tenant_context=ctx,
        order_item_id=glu_item.id,
        status="entered",
        values=[{"analyte_code": "GLU", "raw_value": "450.0"}],
    )

    # Filter with is_critical_only=True
    crit_items, crit_count = get_department_worklist(
        db_session,
        tenant_context=ctx,
        is_critical_only=True,
    )
    assert crit_count == 1
    assert crit_items[0]["has_critical_flag"] is True

    # 3. Worklist summary aggregation
    summary = get_worklist_summary(db_session, tenant_context=ctx)
    assert summary["total_queued"] == 3
    assert summary["pending_entry"] == 2
    assert summary["pending_verification"] == 1
    assert summary["critical_pending"] == 1


def test_worklist_rbac_and_tenant_isolation(db_session: Session):
    env = _setup_worklist_env(db_session)
    ctx1 = env["ctx1"]
    ctx1_unauth = env["ctx1_unauth"]
    ctx2 = env["ctx2"]

    # 1. Unauthorized user cannot access worklist
    with pytest.raises(ForbiddenError):
        get_department_worklist(db_session, tenant_context=ctx1_unauth)

    with pytest.raises(ForbiddenError):
        get_worklist_summary(db_session, tenant_context=ctx1_unauth)

    # 2. Multi-tenant isolation: Tenant 2 sees 0 items from Tenant 1
    t2_items, t2_count = get_department_worklist(db_session, tenant_context=ctx2)
    assert t2_count == 0
    assert len(t2_items) == 0

    t2_summary = get_worklist_summary(db_session, tenant_context=ctx2)
    assert t2_summary["total_queued"] == 0

    # 3. Bounded pagination check
    paged, _ = get_department_worklist(db_session, tenant_context=ctx1, limit=1)
    assert len(paged) == 1


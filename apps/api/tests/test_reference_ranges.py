"""Tests for P05-01: Age/Sex/Context-specific Reference Range Model and Clinical Resolution."""
import uuid
from decimal import Decimal
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.audit.service import get_audit_logs
from app.db import Base
from app.errors import ForbiddenError, NotFoundError, ValidationError
from app.models.core import Branch, Department, Tenant
from app.models.identity import Permission, Role, RolePermission, User, UserRole
from app.models.pathology import Test, TestReferenceRange
from app.pathology.reference_range_service import (
    add_reference_range,
    delete_reference_range,
    evaluate_result_against_range,
    list_reference_ranges,
    resolve_reference_range,
    update_reference_range,
)
from app.pathology.test_master import create_test
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


def _setup_range_env(db: Session):
    tenant1 = Tenant(name="City Diagnostics", code="CD-01", is_active=True)
    tenant2 = Tenant(name="Global Labs", code="GL-02", is_active=True)
    db.add_all([tenant1, tenant2])
    db.flush()

    branch1 = Branch(tenant_id=tenant1.id, name="City Central", code="CC-01", is_active=True)
    branch2 = Branch(tenant_id=tenant2.id, name="Global Main", code="GM-01", is_active=True)
    db.add_all([branch1, branch2])
    db.flush()

    dept1 = Department(tenant_id=tenant1.id, branch_id=branch1.id, name="Biochemistry", code="BIO", is_active=True)
    dept2 = Department(tenant_id=tenant2.id, branch_id=branch2.id, name="Biochemistry", code="BIO", is_active=True)
    db.add_all([dept1, dept2])
    db.flush()

    # Permissions
    perm_view = Permission(code="test.view", module="pathology", resource="test", action="view", risk_level="normal")
    perm_create = Permission(code="test.create", module="pathology", resource="test", action="create", risk_level="normal")
    perm_edit = Permission(code="test.edit", module="pathology", resource="test", action="edit", risk_level="high")
    db.add_all([perm_view, perm_create, perm_edit])
    db.flush()

    # Roles
    role_admin = Role(tenant_id=tenant1.id, name="Pathologist", is_system=False)
    role_viewer = Role(tenant_id=tenant1.id, name="Lab Tech", is_system=False)
    db.add_all([role_admin, role_viewer])
    db.flush()

    db.add_all([
        RolePermission(role_id=role_admin.id, permission_id=perm_view.id, allow=True),
        RolePermission(role_id=role_admin.id, permission_id=perm_create.id, allow=True),
        RolePermission(role_id=role_admin.id, permission_id=perm_edit.id, allow=True),
        RolePermission(role_id=role_viewer.id, permission_id=perm_view.id, allow=True),
    ])

    user_admin = User(tenant_id=tenant1.id, email="doc@city.com", username="pathologist1", hashed_password="pw")
    user_viewer = User(tenant_id=tenant1.id, email="tech@city.com", username="tech1", hashed_password="pw")
    db.add_all([user_admin, user_viewer])
    db.flush()

    db.add_all([
        UserRole(user_id=user_admin.id, role_id=role_admin.id),
        UserRole(user_id=user_viewer.id, role_id=role_viewer.id),
    ])

    # Create tests
    ctx1 = TenantContext(tenant_id=tenant1.id, branch_id=branch1.id, user_id=user_admin.id)
    test_glucose = create_test(
        db,
        tenant_context=ctx1,
        code="GLU",
        name="Blood Glucose",
        display_name="Glucose",
        unit="mg/dL",
        department_id=dept1.id,
    )

    ctx2 = TenantContext(tenant_id=tenant2.id, branch_id=branch2.id, user_id=str(uuid.uuid4()))
    test_t2 = create_test(
        db,
        tenant_context=ctx2,
        code="GLU",
        name="Blood Glucose",
        display_name="Glucose",
        unit="mg/dL",
        department_id=dept2.id,
    )

    db.commit()

    return {
        "tenant1": tenant1,
        "tenant2": tenant2,
        "user_admin": user_admin,
        "user_viewer": user_viewer,
        "ctx1_admin": ctx1,
        "ctx1_viewer": TenantContext(tenant_id=tenant1.id, branch_id=branch1.id, user_id=user_viewer.id),
        "ctx2": ctx2,
        "test_glucose": test_glucose,
        "test_t2": test_t2,
    }


def test_add_and_validate_reference_range(db_session: Session):
    env = _setup_range_env(db_session)
    ctx = env["ctx1_admin"]
    test_id = env["test_glucose"].id

    # 1. Successful creation with age, sex, context, critical thresholds
    rr = add_reference_range(
        db_session,
        tenant_context=ctx,
        test_id=test_id,
        sex="all",
        age_min=18,
        age_max=65,
        age_unit="years",
        context="fasting",
        low_value=70.0,
        high_value=99.0,
        critical_low=45.0,
        critical_high=400.0,
        text_range="70 - 99 mg/dL",
    )
    assert rr.id is not None
    assert rr.context == "fasting"
    assert float(rr.low_value) == 70.0
    assert float(rr.critical_low) == 45.0

    # Verify audit event
    logs = get_audit_logs(db_session, tenant_id=ctx.tenant_id, entity_type="test_reference_range", entity_id=rr.id)
    assert any(log.action_code == "reference_range.created" for log in logs)

    # 2. Validation: negative age
    with pytest.raises(ValidationError):
        add_reference_range(
            db_session,
            tenant_context=ctx,
            test_id=test_id,
            age_min=-5,
        )

    # 3. Validation: age_min > age_max
    with pytest.raises(ValidationError):
        add_reference_range(
            db_session,
            tenant_context=ctx,
            test_id=test_id,
            age_min=50,
            age_max=20,
        )

    # 4. Validation: low_value > high_value
    with pytest.raises(ValidationError):
        add_reference_range(
            db_session,
            tenant_context=ctx,
            test_id=test_id,
            low_value=120.0,
            high_value=80.0,
        )

    # 5. Validation: critical_low > low_value
    with pytest.raises(ValidationError):
        add_reference_range(
            db_session,
            tenant_context=ctx,
            test_id=test_id,
            low_value=70.0,
            critical_low=80.0,
        )

    # 6. Validation: critical_high < high_value
    with pytest.raises(ValidationError):
        add_reference_range(
            db_session,
            tenant_context=ctx,
            test_id=test_id,
            high_value=140.0,
            critical_high=120.0,
        )


def test_reference_range_resolution_age_sex_context(db_session: Session):
    env = _setup_range_env(db_session)
    ctx = env["ctx1_admin"]
    test_id = env["test_glucose"].id

    # Add 4 ranges:
    # 1. Adult Fasting (18-120 yrs, all sex, context=fasting)
    rr_adult_fasting = add_reference_range(
        db_session,
        tenant_context=ctx,
        test_id=test_id,
        sex="all",
        age_min=18,
        age_max=120,
        context="fasting",
        low_value=70.0,
        high_value=99.0,
        critical_low=45.0,
        critical_high=400.0,
        priority=10,
    )

    # 2. Adult Postprandial (18-120 yrs, all sex, context=postprandial)
    rr_adult_pp = add_reference_range(
        db_session,
        tenant_context=ctx,
        test_id=test_id,
        sex="all",
        age_min=18,
        age_max=120,
        context="postprandial",
        low_value=70.0,
        high_value=140.0,
        critical_low=45.0,
        critical_high=400.0,
        priority=10,
    )

    # 3. Pediatric Fasting (0-17 yrs, all sex, context=fasting)
    rr_pediatric = add_reference_range(
        db_session,
        tenant_context=ctx,
        test_id=test_id,
        sex="all",
        age_min=0,
        age_max=17,
        context="fasting",
        low_value=60.0,
        high_value=100.0,
        critical_low=40.0,
        critical_high=350.0,
        priority=10,
    )

    # 4. Neonatal (0-28 days, all sex)
    rr_neonatal = add_reference_range(
        db_session,
        tenant_context=ctx,
        test_id=test_id,
        sex="all",
        age_min=0,
        age_max=28,
        age_unit="days",
        context=None,
        low_value=40.0,
        high_value=90.0,
        priority=5,
    )

    # Test 1: Adult Fasting patient (age 45, fasting)
    resolved_1 = resolve_reference_range(
        db_session,
        tenant_context=ctx,
        test_id=test_id,
        patient_age_years=45,
        context="fasting",
    )
    assert resolved_1.id == rr_adult_fasting.id

    # Test 2: Adult Postprandial patient (age 45, postprandial)
    resolved_2 = resolve_reference_range(
        db_session,
        tenant_context=ctx,
        test_id=test_id,
        patient_age_years=45,
        context="postprandial",
    )
    assert resolved_2.id == rr_adult_pp.id

    # Test 3: Pediatric Fasting patient (age 8, fasting)
    resolved_3 = resolve_reference_range(
        db_session,
        tenant_context=ctx,
        test_id=test_id,
        patient_age_years=8,
        context="fasting",
    )
    assert resolved_3.id == rr_pediatric.id

    # Test 4: Neonate patient (age 10 days)
    resolved_4 = resolve_reference_range(
        db_session,
        tenant_context=ctx,
        test_id=test_id,
        patient_age_days=10,
    )
    assert resolved_4.id == rr_neonatal.id



def test_evaluate_result_against_range(db_session: Session):
    env = _setup_range_env(db_session)
    ctx = env["ctx1_admin"]
    test_id = env["test_glucose"].id

    rr = add_reference_range(
        db_session,
        tenant_context=ctx,
        test_id=test_id,
        low_value=70.0,
        high_value=100.0,
        critical_low=45.0,
        critical_high=400.0,
        text_range="70 - 100 mg/dL",
    )

    # 1. Normal
    eval_norm = evaluate_result_against_range(rr, 85.0)
    assert eval_norm["flag"] == "normal"
    assert not eval_norm["is_abnormal"]
    assert not eval_norm["is_critical"]

    # 2. Borderline low
    eval_low = evaluate_result_against_range(rr, 65.0)
    assert eval_low["flag"] == "low"
    assert eval_low["is_abnormal"]
    assert not eval_low["is_critical"]

    # 3. Critical low (panic)
    eval_crit_low = evaluate_result_against_range(rr, 40.0)
    assert eval_crit_low["flag"] == "critical_low"
    assert eval_crit_low["is_abnormal"]
    assert eval_crit_low["is_critical"]

    # 4. Borderline high
    eval_high = evaluate_result_against_range(rr, 125.0)
    assert eval_high["flag"] == "high"
    assert eval_high["is_abnormal"]
    assert not eval_high["is_critical"]

    # 5. Critical high (panic)
    eval_crit_high = evaluate_result_against_range(rr, 450.0)
    assert eval_crit_high["flag"] == "critical_high"
    assert eval_crit_high["is_abnormal"]
    assert eval_crit_high["is_critical"]


def test_rbac_and_tenant_isolation(db_session: Session):
    env = _setup_range_env(db_session)
    ctx1_admin = env["ctx1_admin"]
    ctx1_viewer = env["ctx1_viewer"]
    ctx2 = env["ctx2"]
    test_id_t1 = env["test_glucose"].id
    test_id_t2 = env["test_t2"].id

    rr1 = add_reference_range(
        db_session,
        tenant_context=ctx1_admin,
        test_id=test_id_t1,
        low_value=70.0,
        high_value=110.0,
    )

    # 1. Viewer can list
    items, count = list_reference_ranges(db_session, tenant_context=ctx1_viewer, test_id=test_id_t1)
    assert count == 1
    assert len(items) == 1

    # 2. Viewer cannot add or edit reference range
    with pytest.raises(ForbiddenError):
        add_reference_range(
            db_session,
            tenant_context=ctx1_viewer,
            test_id=test_id_t1,
            low_value=50.0,
            high_value=90.0,
        )

    with pytest.raises(ForbiddenError):
        update_reference_range(
            db_session,
            tenant_context=ctx1_viewer,
            reference_range_id=rr1.id,
            update_data={"low_value": 75.0},
        )

    # 3. Tenant 2 cannot access Tenant 1 test or reference ranges
    with pytest.raises(NotFoundError):
        list_reference_ranges(db_session, tenant_context=ctx2, test_id=test_id_t1)

    with pytest.raises(NotFoundError):
        update_reference_range(
            db_session,
            tenant_context=ctx2,
            reference_range_id=rr1.id,
            update_data={"low_value": 75.0},
        )

    with pytest.raises(NotFoundError):
        delete_reference_range(
            db_session,
            tenant_context=ctx2,
            reference_range_id=rr1.id,
        )

    # 4. Admin deletes successfully
    delete_reference_range(db_session, tenant_context=ctx1_admin, reference_range_id=rr1.id)
    items_after, count_after = list_reference_ranges(db_session, tenant_context=ctx1_admin, test_id=test_id_t1)
    assert count_after == 0


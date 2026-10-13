"""Tests for P05-04: Abnormal/Critical Engine (Qualitative flagging, delta checks, critical alerts, and acknowledgement workflow)."""
import uuid
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.audit.service import get_audit_logs
from app.db import Base
from app.errors import ConflictError, NotFoundError, ValidationError
from app.models.core import Branch, Department, Tenant
from app.models.identity import Permission, Role, RolePermission, User, UserRole
from app.models.pathology import CriticalAlert, Order, OrderItem, Result, ResultValue, Test
from app.models.patient import Patient
from app.pathology.flagging_engine import (
    acknowledge_critical_alert,
    evaluate_delta_check,
    evaluate_qualitative_flag,
    list_critical_alerts,
    trigger_critical_alerts_for_result,
)
from app.pathology.order_workflow import create_order
from app.pathology.reference_range_service import add_reference_range
from app.pathology.result_service import record_result_values
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


def test_qualitative_flag_rules():
    # Normal values
    assert evaluate_qualitative_flag("Negative") == ("normal", False)
    assert evaluate_qualitative_flag("non-reactive") == ("normal", False)
    assert evaluate_qualitative_flag("Absent") == ("normal", False)
    assert evaluate_qualitative_flag("Clear") == ("normal", False)
    assert evaluate_qualitative_flag("Not Detected") == ("normal", False)

    # Abnormal values
    flag1, crit1 = evaluate_qualitative_flag("Positive")
    assert flag1 == "abnormal"

    flag2, crit2 = evaluate_qualitative_flag("Reactive (HIV 1/2)")
    assert flag2 == "abnormal"
    assert crit2 is True

    flag3, crit3 = evaluate_qualitative_flag("Turbid / Cloudy")
    assert flag3 == "abnormal"


def _setup_clinical_env(db: Session):
    tenant1 = Tenant(name="Metro Labs", code="ML-01", is_active=True)
    tenant2 = Tenant(name="Global Health", code="GH-02", is_active=True)
    db.add_all([tenant1, tenant2])
    db.flush()

    branch1 = Branch(tenant_id=tenant1.id, name="Main Lab", code="ML-01", is_active=True)
    branch2 = Branch(tenant_id=tenant2.id, name="GH Lab", code="GL-01", is_active=True)
    db.add_all([branch1, branch2])
    db.flush()

    dept1 = Department(tenant_id=tenant1.id, branch_id=branch1.id, name="Biochemistry", code="BIO", is_active=True)
    dept2 = Department(tenant_id=tenant2.id, branch_id=branch2.id, name="Biochemistry", code="BIO", is_active=True)
    db.add_all([dept1, dept2])
    db.flush()

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

    role = Role(tenant_id=tenant1.id, name="Technician", is_system=False)
    db.add(role)
    db.flush()
    for p in perms:
        db.add(RolePermission(role_id=role.id, permission_id=p.id, allow=True))

    user = User(tenant_id=tenant1.id, email="tech@metro.com", username="tech_metro", hashed_password="pw")
    db.add(user)
    db.flush()
    db.add(UserRole(user_id=user.id, role_id=role.id))

    ctx1 = TenantContext(tenant_id=tenant1.id, branch_id=branch1.id, user_id=user.id)
    ctx2 = TenantContext(tenant_id=tenant2.id, branch_id=branch2.id, user_id=str(uuid.uuid4()))

    test_k = create_test(
        db,
        tenant_context=ctx1,
        code="K",
        name="Potassium Serum",
        display_name="Potassium",
        unit="mmol/L",
        department_id=dept1.id,
    )
    add_reference_range(
        db,
        tenant_context=ctx1,
        test_id=test_k.id,
        sex="all",
        low_value=3.5,
        high_value=5.1,
        critical_low=2.8,
        critical_high=6.2,
        text_range="3.5 - 5.1 mmol/L",
    )

    pat = register_patient(
        db,
        tenant_context=ctx1,
        first_name="Walter",
        last_name="White",
        sex="male",
    )

    db.commit()

    return {
        "tenant1": tenant1,
        "tenant2": tenant2,
        "ctx1": ctx1,
        "ctx2": ctx2,
        "test_k": test_k,
        "patient": pat,
        "branch1": branch1,
    }


def test_delta_check_evaluation(db_session: Session):
    env = _setup_clinical_env(db_session)
    ctx = env["ctx1"]
    pat = env["patient"]
    test_k = env["test_k"]

    order1 = create_order(db_session, tenant_context=ctx, patient_id=pat.id, test_ids=[test_k.id], branch_id=env["branch1"].id)
    res1 = record_result_values(
        db_session,
        tenant_context=ctx,
        order_item_id=order1.items[0].id,
        status="entered",
        values=[{"analyte_code": "K", "raw_value": "4.0"}],
    )

    check_normal = evaluate_delta_check(
        db_session,
        tenant_id=ctx.tenant_id,
        patient_id=pat.id,
        analyte_code="K",
        current_numeric_value=4.2,
        max_pct_change=50.0,
    )
    assert check_normal["has_prior"] is True
    assert check_normal["delta_flag"] is None
    assert check_normal["is_violation"] is False
    assert check_normal["percent_change"] == 5.0

    check_surge = evaluate_delta_check(
        db_session,
        tenant_id=ctx.tenant_id,
        patient_id=pat.id,
        analyte_code="K",
        current_numeric_value=6.8,
        max_pct_change=50.0,
    )
    assert check_surge["is_violation"] is True
    assert check_surge["delta_flag"] == "DELTA_ALERT"
    assert check_surge["percent_change"] == 70.0



def test_critical_alert_lifecycle(db_session: Session):
    env = _setup_clinical_env(db_session)
    ctx = env["ctx1"]
    ctx2 = env["ctx2"]
    pat = env["patient"]
    test_k = env["test_k"]

    order = create_order(db_session, tenant_context=ctx, patient_id=pat.id, test_ids=[test_k.id], branch_id=env["branch1"].id)
    result = record_result_values(
        db_session,
        tenant_context=ctx,
        order_item_id=order.items[0].id,
        status="entered",
        values=[{"analyte_code": "K", "raw_value": "7.2"}],
    )
    assert result.values[0].critical_flag is True
    assert result.values[0].abnormal_flag == "critical_high"

    alerts = trigger_critical_alerts_for_result(db_session, tenant_context=ctx, result_id=result.id)
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.status == "pending_acknowledgement"
    assert alert.analyte_code == "K"
    assert alert.flag == "critical_high"
    assert alert.value == "7.2"

    logs = get_audit_logs(db_session, tenant_id=ctx.tenant_id, entity_type="critical_alert", entity_id=alert.id)
    assert any(l.action_code == "critical_alert.triggered" for l in logs)

    dup_alerts = trigger_critical_alerts_for_result(db_session, tenant_context=ctx, result_id=result.id)
    assert len(dup_alerts) == 0

    pending_list, count = list_critical_alerts(db_session, tenant_context=ctx, status="pending_acknowledgement")
    assert count == 1
    assert len(pending_list) == 1

    with pytest.raises(ValidationError):
        acknowledge_critical_alert(db_session, tenant_context=ctx, alert_id=alert.id, communicated_to="")

    ack = acknowledge_critical_alert(
        db_session,
        tenant_context=ctx,
        alert_id=alert.id,
        communicated_to="Dr. Gregory House via direct phone line (Ext 4040)",
        notes="Physician notified immediately of severe hyperkalemia; patient placed on telemetry",
    )
    assert ack.status == "acknowledged"
    assert ack.acknowledged_by == ctx.user_id
    assert ack.acknowledged_at is not None
    assert ack.communicated_to == "Dr. Gregory House via direct phone line (Ext 4040)"

    with pytest.raises(ConflictError):
        acknowledge_critical_alert(
            db_session,
            tenant_context=ctx,
            alert_id=alert.id,
            communicated_to="Dr. Wilson",
        )

    t2_alerts, t2_count = list_critical_alerts(db_session, tenant_context=ctx2)
    assert t2_count == 0
    assert len(t2_alerts) == 0

    with pytest.raises(NotFoundError):
        acknowledge_critical_alert(
            db_session,
            tenant_context=ctx2,
            alert_id=alert.id,
            communicated_to="Dr. Someone",
        )


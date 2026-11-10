"""Comprehensive End-to-End Diagnostic Pathology Workflow Test:
Patient -> Test Master & Ranges -> Order -> Sample Lifecycle -> Worklist -> Result Entry -> Formulas -> Critical Alerts -> Verification -> Pathologist Release -> Amendment -> Failure/Invalid Paths.
"""
from __future__ import annotations

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
from app.models.pathology import CriticalAlert, Order, OrderItem, Result, ResultValue, Sample, Test, TestReferenceRange
from app.models.patient import Patient
from app.pathology.calculation_engine import compute_derived_results
from app.pathology.flagging_engine import acknowledge_critical_alert, trigger_critical_alerts_for_result
from app.pathology.order_workflow import create_order
from app.pathology.reference_range_service import add_reference_range
from app.pathology.result_service import (
    amend_result,
    approve_and_release_result,
    get_result,
    get_result_version_history,
    record_result_values,
    verify_result,
)
from app.pathology.sample_workflow import (
    SampleStateTransitionError,
    accept_sample,
    barcode_sample,
    collect_sample,
    create_sample_for_order_item,
    receive_sample,
    reject_sample,
)
from app.pathology.test_master import create_test
from app.pathology.worklist_service import get_department_worklist
from app.patient.service import register_patient
from app.security.tenant_guard import TenantContext


@pytest.fixture
def db_session_factory(tmp_path):
    db_file = tmp_path / "test_pathology_e2e.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False, "timeout": 30},
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    try:
        yield session_factory
    finally:
        try:
            from sqlalchemy.orm import close_all_sessions
            close_all_sessions()
        except Exception:
            pass
        engine.dispose()


def _setup_pathology_e2e_env(session: Session):
    tenant = Tenant(name="National Diagnostic Institute", code="NDI-01", is_active=True)
    tenant2 = Tenant(name="External Competitor Lab", code="ECL-02", is_active=True)
    session.add_all([tenant, tenant2])
    session.flush()

    branch = Branch(tenant_id=tenant.id, name="Central Facility", code="CF-01", is_active=True)
    branch2 = Branch(tenant_id=tenant2.id, name="Branch Ext", code="BX-01", is_active=True)
    session.add_all([branch, branch2])
    session.flush()

    dept = Department(tenant_id=tenant.id, branch_id=branch.id, name="Clinical Chemistry", code="CC", is_active=True)
    session.add(dept)
    session.flush()

    perms = [
        Permission(code="patient.register", module="patient", resource="patient", action="register", risk_level="normal"),
        Permission(code="order.create", module="pathology", resource="order", action="create", risk_level="normal"),
        Permission(code="sample.collect", module="pathology", resource="sample", action="collect", risk_level="normal"),
        Permission(code="sample.receive", module="pathology", resource="sample", action="receive", risk_level="normal"),
        Permission(code="sample.reject", module="pathology", resource="sample", action="reject", risk_level="high"),
        Permission(code="sample.view", module="pathology", resource="sample", action="view", risk_level="normal"),
        Permission(code="result.view", module="pathology", resource="result", action="view", risk_level="normal"),
        Permission(code="result.enter", module="pathology", resource="result", action="enter", risk_level="normal"),
        Permission(code="result.verify", module="pathology", resource="result", action="verify", risk_level="high"),
        Permission(code="result.approve", module="pathology", resource="result", action="approve", risk_level="critical"),
        Permission(code="result.edit", module="pathology", resource="result", action="edit", risk_level="high"),
        Permission(code="test.create", module="pathology", resource="test", action="create", risk_level="normal"),
    ]
    session.add_all(perms)
    session.flush()

    # Roles: Pathologist, Technician, Unauthorized
    role_pathologist = Role(tenant_id=tenant.id, name="Pathologist", is_system=False)
    role_tech = Role(tenant_id=tenant.id, name="Technician", is_system=False)
    role_reception = Role(tenant_id=tenant.id, name="Receptionist", is_system=False)
    session.add_all([role_pathologist, role_tech, role_reception])
    session.flush()

    for p in perms:
        session.add(RolePermission(role_id=role_pathologist.id, permission_id=p.id, allow=True))
        if p.code != "result.approve":
            session.add(RolePermission(role_id=role_tech.id, permission_id=p.id, allow=True))
        if p.code in ("patient.register", "order.create", "result.view"):
            session.add(RolePermission(role_id=role_reception.id, permission_id=p.id, allow=True))

    user_path = User(tenant_id=tenant.id, email="path@ndi.com", username="dr_path", hashed_password="pw")
    user_tech = User(tenant_id=tenant.id, email="tech@ndi.com", username="tech_jim", hashed_password="pw")
    user_recep = User(tenant_id=tenant.id, email="recep@ndi.com", username="recep_ann", hashed_password="pw")
    session.add_all([user_path, user_tech, user_recep])
    session.flush()

    session.add_all([
        UserRole(user_id=user_path.id, role_id=role_pathologist.id),
        UserRole(user_id=user_tech.id, role_id=role_tech.id),
        UserRole(user_id=user_recep.id, role_id=role_reception.id),
    ])

    ctx_path = TenantContext(tenant_id=tenant.id, branch_id=branch.id, user_id=user_path.id)
    ctx_tech = TenantContext(tenant_id=tenant.id, branch_id=branch.id, user_id=user_tech.id)
    ctx_recep = TenantContext(tenant_id=tenant.id, branch_id=branch.id, user_id=user_recep.id)
    ctx_ext = TenantContext(tenant_id=tenant2.id, branch_id=branch2.id, user_id=str(uuid.uuid4()))

    # Master test: Potassium (with critical flags)
    test_k = create_test(
        session,
        tenant_context=ctx_path,
        code="K",
        name="Potassium Serum",
        display_name="Potassium",
        unit="mmol/L",
        department_id=dept.id,
    )
    add_reference_range(
        session,
        tenant_context=ctx_path,
        test_id=test_k.id,
        sex="all",
        low_value=3.5,
        high_value=5.1,
        critical_low=2.8,
        critical_high=6.2,
        text_range="3.5 - 5.1 mmol/L",
    )

    # Master tests for calculation: Total Protein, Albumin, Globulin (calculated)
    test_tp = create_test(session, tenant_context=ctx_path, code="TP", name="Total Protein", display_name="TP", unit="g/dL", department_id=dept.id)
    test_alb = create_test(session, tenant_context=ctx_path, code="ALB", name="Albumin", display_name="Albumin", unit="g/dL", department_id=dept.id)
    test_glob = create_test(
        session,
        tenant_context=ctx_path,
        code="GLOB",
        name="Globulin",
        display_name="Globulin",
        unit="g/dL",
        department_id=dept.id,
        is_calculated=True,
        calculation_formula="TP - ALB",
        decimal_precision=2,
    )
    add_reference_range(session, tenant_context=ctx_path, test_id=test_glob.id, sex="all", low_value=2.0, high_value=3.5, text_range="2.0 - 3.5 g/dL")

    session.commit()

    return {
        "tenant": tenant,
        "branch": branch,
        "dept": dept,
        "ctx_path": ctx_path,
        "ctx_tech": ctx_tech,
        "ctx_recep": ctx_recep,
        "ctx_ext": ctx_ext,
        "test_k": test_k,
        "test_tp": test_tp,
        "test_alb": test_alb,
        "test_glob": test_glob,
    }



def test_full_diagnostic_pathology_lifecycle_e2e(db_session_factory):
    session = db_session_factory()
    env = _setup_pathology_e2e_env(session)
    ctx_path = env["ctx_path"]
    ctx_tech = env["ctx_tech"]
    ctx_recep = env["ctx_recep"]

    # 1. Patient Registration
    patient = register_patient(
        session,
        tenant_context=ctx_recep,
        first_name="Leonardo",
        last_name="DaVinci",
        sex="male",
        date_of_birth=date(1975, 4, 15),
    )
    assert patient.id is not None

    # 2. Diagnostic Order Creation
    order = create_order(
        session,
        tenant_context=ctx_recep,
        patient_id=patient.id,
        test_ids=[env["test_k"].id, env["test_tp"].id, env["test_alb"].id, env["test_glob"].id],
        branch_id=env["branch"].id,
    )
    assert len(order.items) == 4
    item_k = next(it for it in order.items if it.test_id == env["test_k"].id)
    item_tp = next(it for it in order.items if it.test_id == env["test_tp"].id)

    # 3. Sample Lifecycle: Collect -> Barcode -> Receive -> Accept
    sample_k = create_sample_for_order_item(session, tenant_context=ctx_tech, order_item_id=item_k.id, specimen_type="Serum")
    sample_k = collect_sample(session, tenant_context=ctx_tech, sample_id=sample_k.id)
    sample_k = barcode_sample(session, tenant_context=ctx_tech, sample_id=sample_k.id, barcode="SMP-K-001")
    sample_k = receive_sample(session, tenant_context=ctx_tech, sample_id=sample_k.id)
    sample_k = accept_sample(session, tenant_context=ctx_tech, sample_id=sample_k.id)
    assert sample_k.status == "accepted"

    # 4. Worklist Pickup
    worklist_items, count = get_department_worklist(
        session,
        tenant_context=ctx_tech,
        department_id=env["dept"].id,
        status="pending_entry",
    )
    assert count == 4
    assert any(it["order_item_id"] == item_k.id for it in worklist_items)

    # 5. Result Entry: Enter critical panic potassium value (7.0 mmol/L)
    res_k = record_result_values(
        session,
        tenant_context=ctx_tech,
        order_item_id=item_k.id,
        sample_id=sample_k.id,
        status="entered",
        values=[{"analyte_code": "K", "raw_value": "7.0"}],
    )
    assert res_k.status == "entered"
    assert res_k.values[0].abnormal_flag == "critical_high"
    assert res_k.values[0].critical_flag is True

    # 6. Critical Alert Generation and Communication
    alerts = trigger_critical_alerts_for_result(session, tenant_context=ctx_tech, result_id=res_k.id)
    assert len(alerts) == 1
    ack = acknowledge_critical_alert(
        session,
        tenant_context=ctx_tech,
        alert_id=alerts[0].id,
        communicated_to="Dr. Verrocchio via phone line 102",
        notes="Physician notified immediately of severe hyperkalemia",
    )
    assert ack.status == "acknowledged"

    # 7. Enter Protein and Albumin, execute Calculation Engine for Globulin
    res_protein = record_result_values(
        session,
        tenant_context=ctx_tech,
        order_item_id=item_tp.id,
        status="entered",
        values=[
            {"analyte_code": "TP", "raw_value": "7.2"},
            {"analyte_code": "ALB", "raw_value": "4.2"},
        ],
    )
    derived = compute_derived_results(session, tenant_context=ctx_tech, result_id=res_protein.id)
    assert len(derived) == 1
    assert derived[0].analyte_code == "GLOB"
    assert float(derived[0].numeric_value) == 3.00

    # 8. Technician Verification
    v_res_k = verify_result(session, tenant_context=ctx_tech, result_id=res_k.id, notes="Repeated on ISE analyzer confirmed 7.0 mmol/L")
    assert v_res_k.status == "verified"
    assert v_res_k.verified_by == ctx_tech.user_id

    # 9. Pathologist Approval and Digital Release
    released_k = approve_and_release_result(
        session,
        tenant_context=ctx_path,
        result_id=res_k.id,
        notes="Severe hyperkalemia verified and clinically discussed with attending",
    )
    assert released_k.status == "released"
    assert released_k.signature_hash is not None
    assert len(released_k.signature_hash) == 64
    session.refresh(item_k)
    assert item_k.status == "completed"

    # 10. Amendment Lifecycle: Clinician requests re-eval with whole-blood hemolyzed correction
    amended_v2 = amend_result(
        session,
        tenant_context=ctx_path,
        result_id=released_k.id,
        amendment_reason="Re-drawn unhemolyzed venous sample confirmed true K is 4.8 mmol/L",
        updated_values=[{"analyte_code": "K", "raw_value": "4.8"}],
    )
    assert amended_v2.version == 2
    assert amended_v2.status == "entered"
    assert float(amended_v2.values[0].numeric_value) == 4.8

    # Ensure Version 1 remained immutable in database
    session.refresh(released_k)
    assert released_k.version == 1
    assert released_k.status == "amended"
    assert float(released_k.values[0].numeric_value) == 7.0

    # Version history query
    history = get_result_version_history(session, tenant_context=ctx_path, order_item_id=item_k.id)
    assert len(history) == 2
    assert history[0].version == 1
    assert history[1].version == 2



def test_failure_and_invalid_state_transitions(db_session_factory):
    session = db_session_factory()
    env = _setup_pathology_e2e_env(session)
    ctx_path = env["ctx_path"]
    ctx_tech = env["ctx_tech"]
    ctx_recep = env["ctx_recep"]
    ctx_ext = env["ctx_ext"]

    pat = register_patient(session, tenant_context=ctx_recep, first_name="Galileo", last_name="Galilei", sex="male")
    order = create_order(session, tenant_context=ctx_recep, patient_id=pat.id, test_ids=[env["test_k"].id], branch_id=env["branch"].id)
    item = order.items[0]

    # Negative Case 1: Sample Rejection requires mandatory reason
    sample = create_sample_for_order_item(session, tenant_context=ctx_tech, order_item_id=item.id)
    collect_sample(session, tenant_context=ctx_tech, sample_id=sample.id)
    barcode_sample(session, tenant_context=ctx_tech, sample_id=sample.id, barcode="SMP-GAL-001")
    receive_sample(session, tenant_context=ctx_tech, sample_id=sample.id)

    with pytest.raises(SampleStateTransitionError):
        reject_sample(session, tenant_context=ctx_tech, sample_id=sample.id, reason="   ")

    rejected_s = reject_sample(session, tenant_context=ctx_tech, sample_id=sample.id, reason="Gross hemolysis visible in tube")
    assert rejected_s.status == "rejected"

    # Negative Case 2: Receptionist cannot enter results (ForbiddenError)
    with pytest.raises(ForbiddenError):
        record_result_values(
            session,
            tenant_context=ctx_recep,
            order_item_id=item.id,
            status="entered",
            values=[{"analyte_code": "K", "raw_value": "4.1"}],
        )

    # Tech enters result
    res = record_result_values(
        session,
        tenant_context=ctx_tech,
        order_item_id=item.id,
        status="entered",
        values=[{"analyte_code": "K", "raw_value": "4.1"}],
    )

    # Negative Case 3: Pathologist cannot approve an unverified result (must be verified first)
    with pytest.raises(ConflictError):
        approve_and_release_result(session, tenant_context=ctx_path, result_id=res.id)

    # Technician verifies
    verify_result(session, tenant_context=ctx_tech, result_id=res.id)

    # Negative Case 4: Technician cannot approve result (requires result.approve)
    with pytest.raises(ForbiddenError):
        approve_and_release_result(session, tenant_context=ctx_tech, result_id=res.id)

    # Pathologist approves and releases
    approve_and_release_result(session, tenant_context=ctx_path, result_id=res.id)

    # Negative Case 5: Direct edit on released result is blocked (must use amendment)
    with pytest.raises(ConflictError):
        record_result_values(
            session,
            tenant_context=ctx_tech,
            order_item_id=item.id,
            values=[{"analyte_code": "K", "raw_value": "4.5"}],
        )

    # Negative Case 6: Cross-tenant isolation (Tenant 2 cannot read or amend Tenant 1 result)
    with pytest.raises(NotFoundError):
        get_result(session, tenant_context=ctx_ext, result_id=res.id)

    with pytest.raises(NotFoundError):
        amend_result(session, tenant_context=ctx_ext, result_id=res.id, amendment_reason="Compromise attempt")


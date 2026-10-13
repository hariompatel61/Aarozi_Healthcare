"""Tests for P06-06: Report HTML Preview and Offline PDF Render Pipeline."""
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.audit.service import get_audit_logs
from app.db import Base
from app.errors import NotFoundError
from app.models.billing import ReferralPartner
from app.models.core import Branch, Department, Tenant
from app.models.identity import Permission, Role, RolePermission, User, UserRole
from app.models.pathology import Order, OrderItem, Result, ResultValue, Sample, Test
from app.models.patient import Patient
from app.models.reporting import ReportTemplate
from app.pathology.order_workflow import create_order
from app.pathology.result_service import approve_and_release_result, record_result_values, verify_result
from app.pathology.sample_workflow import accept_sample, barcode_sample, collect_sample, create_sample_for_order_item, receive_sample
from app.pathology.test_master import create_test
from app.patient.service import register_patient
from app.reporting.designer_primitives import build_default_template
from app.reporting.render_pipeline import (
    generate_report_document,
    render_report_html,
    render_report_pdf,
)
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


def _setup_render_env(db: Session):
    t1 = Tenant(name="Premier Diagnostics", code="PD-01", is_active=True)
    t2 = Tenant(name="Apex Diagnostics", code="AD-02", is_active=True)
    db.add_all([t1, t2])
    db.flush()

    branch = Branch(tenant_id=t1.id, name="City Central Branch", code="CC-01", is_active=True)
    db.add(branch)
    db.flush()

    dept = Department(tenant_id=t1.id, branch_id=branch.id, name="Biochemistry", code="BIO", is_active=True)
    db.add(dept)
    db.flush()

    perms = [
        Permission(code="result.view", module="pathology", resource="result", action="view", risk_level="normal"),
        Permission(code="result.enter", module="pathology", resource="result", action="enter", risk_level="normal"),
        Permission(code="result.verify", module="pathology", resource="result", action="verify", risk_level="high"),
        Permission(code="result.approve", module="pathology", resource="result", action="approve", risk_level="critical"),
        Permission(code="order.create", module="pathology", resource="order", action="create", risk_level="normal"),
        Permission(code="patient.register", module="patient", resource="patient", action="register", risk_level="normal"),
        Permission(code="test.create", module="pathology", resource="test", action="create", risk_level="normal"),
        Permission(code="report.view", module="reporting", resource="report", action="view", risk_level="normal"),
    ]
    db.add_all(perms)
    db.flush()

    role = Role(tenant_id=t1.id, name="Pathologist", is_system=False)
    db.add(role)
    db.flush()
    for p in perms:
        db.add(RolePermission(role_id=role.id, permission_id=p.id, allow=True))

    user = User(tenant_id=t1.id, email="doc@premier.com", username="dr_premier", hashed_password="pw")
    db.add(user)
    db.flush()
    db.add(UserRole(user_id=user.id, role_id=role.id))

    ctx1 = TenantContext(tenant_id=t1.id, branch_id=branch.id, user_id=user.id)
    ctx2 = TenantContext(tenant_id=t2.id, user_id=str(uuid.uuid4()))

    test_cbc = create_test(
        db,
        tenant_context=ctx1,
        code="CBC",
        name="Complete Blood Count",
        display_name="CBC",
        department_id=dept.id,
    )

    pat = register_patient(db, tenant_context=ctx1, first_name="Grace", last_name="Hopper", sex="female", date_of_birth=date(1982, 12, 9))
    order = create_order(db, tenant_context=ctx1, patient_id=pat.id, test_ids=[test_cbc.id], branch_id=branch.id)

    res = record_result_values(
        db,
        tenant_context=ctx1,
        order_item_id=order.items[0].id,
        status="entered",
        values=[
            {"analyte_code": "HGB", "raw_value": "13.5", "abnormal_flag": "normal", "reference_text": "12.0 - 15.5 g/dL"},
            {"analyte_code": "WBC", "raw_value": "14.2", "abnormal_flag": "high", "reference_text": "4.5 - 11.0 10^3/uL"},
        ],
    )
    verify_result(db, tenant_context=ctx1, result_id=res.id)
    approve_and_release_result(db, tenant_context=ctx1, result_id=res.id, notes="Leukocytosis noted. Clinically correlate.")

    db.commit()

    return {
        "ctx1": ctx1,
        "ctx2": ctx2,
        "result": res,
    }


def test_html_and_pdf_report_rendering(db_session: Session):
    env = _setup_render_env(db_session)
    ctx1 = env["ctx1"]
    ctx2 = env["ctx2"]
    res = env["result"]

    # 1. Generate HTML Document
    doc_html = generate_report_document(
        db_session,
        tenant_context=ctx1,
        result_id=res.id,
        output_format="html",
    )
    assert doc_html["content_type"] == "text/html"
    assert "<!DOCTYPE html>" in doc_html["payload"]
    assert "Grace Hopper" in doc_html["payload"]
    assert "Complete Blood Count" in doc_html["payload"]
    assert "HGB" in doc_html["payload"]
    assert "WBC" in doc_html["payload"]
    assert "HIGH" in doc_html["payload"]
    assert "Leukocytosis" in doc_html["payload"]

    # Verify audit event
    logs = get_audit_logs(db_session, tenant_id=ctx1.tenant_id, entity_type="result", entity_id=res.id)
    assert any(l.action_code == "report.rendered" for l in logs)

    # 2. Generate Offline Binary PDF Document
    doc_pdf = generate_report_document(
        db_session,
        tenant_context=ctx1,
        result_id=res.id,
        output_format="pdf",
    )
    assert doc_pdf["content_type"] == "application/pdf"
    pdf_bytes = doc_pdf["payload"]
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-1.4")
    assert b"%%EOF" in pdf_bytes

    # 3. Multi-tenant isolation: Tenant 2 cannot render Tenant 1 result report
    with pytest.raises(NotFoundError):
        generate_report_document(db_session, tenant_context=ctx2, result_id=res.id, output_format="html")


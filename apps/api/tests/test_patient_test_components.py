"""Tests for P06-03: Reusable Report Data Components (Patient Header, Test Table, Context Assembly)."""
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.errors import NotFoundError
from app.models.billing import ReferralPartner
from app.models.core import Branch, Department, Tenant
from app.models.identity import Permission, Role, RolePermission, User, UserRole
from app.models.pathology import Order, OrderItem, Result, ResultValue, Sample, Test
from app.models.patient import Patient
from app.pathology.order_workflow import create_order
from app.pathology.result_service import approve_and_release_result, record_result_values, verify_result
from app.pathology.sample_workflow import accept_sample, barcode_sample, collect_sample, create_sample_for_order_item, receive_sample
from app.pathology.test_master import create_test
from app.patient.service import register_patient
from app.reporting.component_assembler import (
    assemble_patient_header_component,
    assemble_report_data_context,
    assemble_test_table_component,
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


def _setup_component_env(db: Session):
    t1 = Tenant(name="Metro Diagnostic Labs", code="MDL-01", is_active=True)
    t2 = Tenant(name="Global Labs", code="GL-02", is_active=True)
    db.add_all([t1, t2])
    db.flush()

    b1 = Branch(tenant_id=t1.id, name="City Central Branch", code="CC-01", is_active=True)
    b2 = Branch(tenant_id=t2.id, name="Global Branch", code="GB-01", is_active=True)
    db.add_all([b1, b2])
    db.flush()

    dept = Department(tenant_id=t1.id, branch_id=b1.id, name="Biochemistry", code="BIO", is_active=True)
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
        Permission(code="sample.collect", module="pathology", resource="sample", action="collect", risk_level="normal"),
        Permission(code="sample.receive", module="pathology", resource="sample", action="receive", risk_level="normal"),
    ]
    db.add_all(perms)
    db.flush()

    role = Role(tenant_id=t1.id, name="Pathologist", is_system=False)
    db.add(role)
    db.flush()
    for p in perms:
        db.add(RolePermission(role_id=role.id, permission_id=p.id, allow=True))

    user = User(tenant_id=t1.id, email="doc@metro.com", username="dr_metro", hashed_password="pw")
    db.add(user)
    db.flush()
    db.add(UserRole(user_id=user.id, role_id=role.id))

    ctx1 = TenantContext(tenant_id=t1.id, branch_id=b1.id, user_id=user.id)
    ctx2 = TenantContext(tenant_id=t2.id, branch_id=b2.id, user_id=str(uuid.uuid4()))

    test_lipid = create_test(
        db,
        tenant_context=ctx1,
        code="LIPID",
        name="Lipid Profile",
        display_name="Lipid",
        unit="mg/dL",
        department_id=dept.id,
    )

    partner = ReferralPartner(tenant_id=t1.id, partner_type="doctor", name="Dr. Gregory House")
    db.add(partner)
    db.flush()

    pat = register_patient(db, tenant_context=ctx1, first_name="Nikola", last_name="Tesla", sex="male", date_of_birth=date(1985, 7, 10))
    order = create_order(db, tenant_context=ctx1, patient_id=pat.id, test_ids=[test_lipid.id], referral_partner_id=partner.id, branch_id=b1.id)

    sample = create_sample_for_order_item(db, tenant_context=ctx1, order_item_id=order.items[0].id, specimen_type="Serum")
    collect_sample(db, tenant_context=ctx1, sample_id=sample.id)
    barcode_sample(db, tenant_context=ctx1, sample_id=sample.id, barcode="SMP-LIP-990")
    receive_sample(db, tenant_context=ctx1, sample_id=sample.id)
    accept_sample(db, tenant_context=ctx1, sample_id=sample.id)

    res = record_result_values(
        db,
        tenant_context=ctx1,
        order_item_id=order.items[0].id,
        sample_id=sample.id,
        status="entered",
        values=[
            {"analyte_code": "CHOL", "raw_value": "210.0", "abnormal_flag": "high", "reference_text": "< 200 mg/dL"},
            {"analyte_code": "TRIG", "raw_value": "140.0", "abnormal_flag": "normal", "reference_text": "< 150 mg/dL"},
        ],
    )
    verify_result(db, tenant_context=ctx1, result_id=res.id)
    approve_and_release_result(db, tenant_context=ctx1, result_id=res.id, notes="Mild hypercholesterolemia noted.")

    db.commit()

    return {
        "ctx1": ctx1,
        "ctx2": ctx2,
        "patient": pat,
        "order": order,
        "sample": sample,
        "result": res,
        "partner": partner,
        "branch": b1,
    }


def test_assemble_patient_header_component(db_session: Session):
    env = _setup_component_env(db_session)
    header = assemble_patient_header_component(
        patient=env["patient"],
        order=env["order"],
        sample=env["sample"],
        referral_partner=env["partner"],
        branch=env["branch"],
    )

    assert header["patient_no"] == env["patient"].patient_no
    assert "Nikola Tesla" in header["full_name"]
    assert header["sex"] == "Male"
    assert "yrs" in header["age"]
    assert header["order_no"] == env["order"].order_no
    assert header["barcode"] == "SMP-LIP-990"
    assert header["referral_partner"]["name"] == "Dr. Gregory House"
    assert header["branch"]["name"] == "City Central Branch"


def test_assemble_test_table_component(db_session: Session):
    env = _setup_component_env(db_session)
    order_item = env["order"].items[0]
    result = env["result"]

    table_data = assemble_test_table_component(result, order_item)
    assert table_data["test_code"] == "LIPID"
    assert len(table_data["analytes"]) == 2

    chol = next(a for a in table_data["analytes"] if a["code"] == "CHOL")
    assert chol["raw_value"] == "210.0"
    assert float(chol["numeric_value"]) == 210.0
    assert chol["flag"] == "HIGH"
    assert chol["is_abnormal"] is True

    trig = next(a for a in table_data["analytes"] if a["code"] == "TRIG")
    assert trig["flag"] == "NORMAL"
    assert trig["is_abnormal"] is False


def test_assemble_report_data_context_and_tenant_isolation(db_session: Session):
    env = _setup_component_env(db_session)
    ctx1 = env["ctx1"]
    ctx2 = env["ctx2"]
    res = env["result"]

    # 1. Successful context assembly for Tenant 1
    context = assemble_report_data_context(db_session, tenant_context=ctx1, result_id=res.id)
    assert "patient_header" in context
    assert "test_table" in context
    assert "clinical_summary" in context
    assert context["clinical_summary"]["status"] == "released"
    assert context["clinical_summary"]["signature_hash"] is not None
    assert "hypercholesterolemia" in context["clinical_summary"]["notes"]

    # 2. Multi-tenant isolation: Tenant 2 cannot assemble context for Tenant 1 result
    with pytest.raises(NotFoundError):
        assemble_report_data_context(db_session, tenant_context=ctx2, result_id=res.id)


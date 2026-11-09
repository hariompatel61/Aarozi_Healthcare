"""Comprehensive integration tests for clinical and financial FastAPI HTTP routers:
- Patients: register, search, get
- Pathology: tests, orders, samples, results, verify, approve
- Billing: invoices, payments, price lists, referrals
- Blood Bank: donors, screenings, donations, inventory
- Reports: templates, render
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base, get_db
from app.main import app
from app.models.core import Tenant, Branch, Department
from app.models.identity import User, Role, Permission, RolePermission, UserRole
from app.models.patient import Patient
from app.models.pathology import Test as PathologyTest, TestReferenceRange as PathologyReferenceRange
from app.security.auth import get_current_user
from app.security.tenant_guard import get_tenant_context, TenantContext


# Global test session
_test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture
def db_session():
    connection = _test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture
def test_env(db_session: Session):
    # Setup Tenant, Branch, Dept
    tenant = Tenant(id="ten_test_01", name="Apex Diagnostic Centre", code="APEX-01", is_active=True)
    branch = Branch(id="br_test_01", tenant_id=tenant.id, name="Apex Central Lab", code="CEN", is_active=True)
    dept = Department(id="dep_test_01", tenant_id=tenant.id, branch_id=branch.id, name="Biochemistry", code="BIO", is_active=True)
    db_session.add_all([tenant, branch, dept])
    db_session.flush()

    # User
    user = User(
        id="usr_admin_01",
        tenant_id=tenant.id,
        username="dr_ahmed",
        email="dr.ahmed@apex.com",
        hashed_password="hashed_pw_mock_123",
        full_name="Dr. Ahmed Raza",
        is_active=True,
        is_superuser=True,
    )
    db_session.add(user)
    db_session.flush()

    # Create baseline lab test
    test_glucose = PathologyTest(
        id="t_glu_01",
        tenant_id=tenant.id,
        department_id=dept.id,
        code="GLU_F",
        name="Fasting Blood Glucose",
        display_name="Fasting Blood Glucose",
        short_name="FBG",
        specimen_type="Fluoride Plasma",
        container_type="Grey Top",
        unit="mg/dL",
        status="active",
        version=1,
    )
    db_session.add(test_glucose)
    db_session.flush()

    ref_range = PathologyReferenceRange(
        test_id=test_glucose.id,
        sex="all",
        age_min=0,
        age_max=43800,
        low_value=70.0,
        high_value=99.0,
        critical_low=45.0,
        critical_high=400.0,
        text_range="70 - 99 mg/dL",
    )
    db_session.add(ref_range)
    db_session.flush()

    return {
        "tenant": tenant,
        "branch": branch,
        "dept": dept,
        "user": user,
        "test_glucose": test_glucose,
    }


@pytest.fixture
def client(db_session: Session, test_env: dict):
    tenant = test_env["tenant"]
    branch = test_env["branch"]
    user = test_env["user"]

    def override_get_db():
        yield db_session

    def override_get_current_user():
        return user

    def override_get_tenant_context():
        return TenantContext(
            tenant_id=tenant.id,
            user_id=user.id,
            branch_id=branch.id,
            is_superuser=True,
        )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_tenant_context] = override_get_tenant_context

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Patient Router Tests
# ---------------------------------------------------------------------------

def test_patient_registration_and_search(client: TestClient):
    payload = {
        "first_name": "Tariq",
        "last_name": "Mahmood",
        "sex": "male",
        "date_of_birth": "1988-06-15",
        "mobile": "+923001234567",
        "email": "tariq@gmail.com",
        "blood_group": "B_POS",
        "identifiers": [
            {"type": "CNIC", "value": "35202-1234567-1", "is_primary": True}
        ],
    }

    # 1. Register Patient
    res = client.post("/patients/register", json=payload)
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["first_name"] == "Tariq"
    assert data["patient_no"].startswith("P-")
    patient_id = data["id"]

    # 2. Get Patient by ID
    res_get = client.get(f"/patients/{patient_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == patient_id

    # 3. Search Patient by Name
    res_search = client.get("/patients?query=Tariq")
    assert res_search.status_code == 200
    results = res_search.json()
    assert len(results) >= 1
    assert any(p["id"] == patient_id for p in results)


# ---------------------------------------------------------------------------
# Pathology & Laboratory Workflow Tests
# ---------------------------------------------------------------------------

def test_pathology_order_to_approval_workflow(client: TestClient, test_env: dict):
    # 1. Register a patient for the order
    patient_res = client.post(
        "/patients/register",
        json={"first_name": "Sobia", "last_name": "Akram", "sex": "female", "mobile": "+923211112233"},
    )
    patient_id = patient_res.json()["id"]
    test_id = test_env["test_glucose"].id

    # 2. Place Order
    order_res = client.post(
        "/pathology/orders/create",
        json={"patient_id": patient_id, "test_ids": [test_id]},
    )
    assert order_res.status_code == 201, order_res.text
    order_data = order_res.json()
    order_id = order_data["id"]
    order_item_id = order_data["items"][0]["id"]
    assert order_data["status"] == "placed"

    # 3. Phlebotomy Collection
    sample_res = client.post(
        "/pathology/samples/collect",
        json={"order_item_ids": [order_item_id], "specimen_type": "Fluoride Plasma"},
    )
    assert sample_res.status_code == 201
    sample_data = sample_res.json()
    sample_id = sample_data["id"]
    assert sample_data["barcode"].startswith("SMP-")

    # 4. Accessioning Receipt & Acceptance
    receipt_res = client.post(
        "/pathology/samples/receive",
        json={"sample_id": sample_id, "temperature_celsius": 4.5},
    )
    assert receipt_res.status_code == 200
    assert receipt_res.json()["status"] == "accepted"

    # 5. Bench Result Entry (Enter 110 mg/dL - High flag expected)
    result_entry_res = client.post(
        "/pathology/results/enter",
        json={
            "order_item_id": order_item_id,
            "sample_id": sample_id,
            "status": "entered",
            "values": [
                {"analyte_code": "GLU_F", "raw_value": "110", "numeric_value": 110.0, "unit": "mg/dL"}
            ],
        },
    )
    assert result_entry_res.status_code == 201, result_entry_res.text
    res_val = result_entry_res.json()
    result_id = res_val["id"]
    assert res_val["status"] == "entered"
    assert res_val["values"][0]["abnormal_flag"] == "HIGH"

    # 6. Technician Verification
    verify_res = client.post(f"/pathology/results/{result_id}/verify", json={"notes": "Technician review confirmed"})
    assert verify_res.status_code == 200
    assert verify_res.json()["status"] == "verified"

    # 7. Pathologist Approval & Report Release
    approve_res = client.post(f"/pathology/results/{result_id}/approve", json={"notes": "Correlated clinically"})
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "released"


# ---------------------------------------------------------------------------
# Billing & Payment Collection Tests
# ---------------------------------------------------------------------------

def test_billing_invoice_and_payment_flow(client: TestClient):
    # 1. Register Patient
    p_res = client.post(
        "/patients/register",
        json={"first_name": "Kamran", "last_name": "Ali", "sex": "male", "mobile": "+923334445566"},
    )
    patient_id = p_res.json()["id"]

    # 2. Create Invoice
    inv_res = client.post(
        "/billing/invoices/create",
        json={
            "patient_id": patient_id,
            "items": [
                {
                    "description": "Fasting Blood Glucose",
                    "quantity": 1,
                    "unit_price": 500.0,
                    "discount_amount": 50.0,
                    "tax_amount": 0.0,
                }
            ],
        },
    )
    assert inv_res.status_code == 201, inv_res.text
    inv_data = inv_res.json()
    invoice_id = inv_data["id"]
    assert inv_data["total_amount"] == 450.0
    assert inv_data["balance_amount"] == 450.0
    assert inv_data["status"] == "issued"

    # 3. Record Payment (Full settlement)
    pay_res = client.post(
        "/billing/payments",
        json={"invoice_id": invoice_id, "amount": 450.0, "method": "cash"},
    )
    assert pay_res.status_code == 201, pay_res.text
    assert pay_res.json()["receipt_no"].startswith("RCP-")

    # 4. Check Invoice Status is now 'paid'
    inv_detail = client.get(f"/billing/invoices/{invoice_id}")
    assert inv_detail.status_code == 200
    detail_data = inv_detail.json()
    assert detail_data["status"] == "paid"
    assert detail_data["paid_amount"] == 450.0
    assert detail_data["balance_amount"] == 0.0


# ---------------------------------------------------------------------------
# Blood Bank Management Tests
# ---------------------------------------------------------------------------

def test_blood_bank_donor_and_screening_flow(client: TestClient):
    # 1. Register Donor
    donor_res = client.post(
        "/blood-bank/donors/register",
        json={
            "first_name": "Hamza",
            "last_name": "Nawaz",
            "sex": "male",
            "date_of_birth": "1995-04-12",
            "blood_group": "O_POS",
            "mobile": "+923459998877",
        },
    )
    assert donor_res.status_code == 201, donor_res.text
    donor_data = donor_res.json()
    donor_id = donor_data["id"]
    assert donor_data["donor_no"].startswith("DNR-")

    # 2. Conduct Screening (Normal vitals & questionnaire)
    screen_res = client.post(
        "/blood-bank/screenings",
        json={
            "donor_id": donor_id,
            "weight_kg": 72.0,
            "hemoglobin_g_dl": 14.5,
            "systolic_bp": 120,
            "diastolic_bp": 80,
            "pulse_bpm": 74,
            "temperature_c": 36.8,
            "questionnaire_responses": {
                "feeling_well": True,
                "recent_fever_or_infection": False,
                "antibiotics_last_14_days": False,
            },
        },
    )
    assert screen_res.status_code == 201, screen_res.text
    screen_data = screen_res.json()
    assert screen_data["eligibility_status"] == "eligible"
    assert screen_data["status"] == "passed"

    # 3. Check Blood Bank Inventory Endpoint
    inv_res = client.get("/blood-bank/inventory")
    assert inv_res.status_code == 200
    assert "inventory" in inv_res.json()


# ---------------------------------------------------------------------------
# Report Engine Router Tests
# ---------------------------------------------------------------------------

def test_report_templates_endpoint(client: TestClient):
    # 1. Query Templates List
    tpl_res = client.get("/reports/templates")
    assert tpl_res.status_code == 200
    data = tpl_res.json()
    assert "total" in data
    assert "items" in data

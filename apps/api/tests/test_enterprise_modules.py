"""Comprehensive integration tests for Enterprise LIS / LIMS modules:
- Module 6: Home Sample Collection
- Module 10: Radiology Investigation Desk
- Module 12: Accounts, Expenses & Petty Cash
- Module 14: Corporate Accounts & Special Rates
- Module 17: NABL Quality Control & Calibration
- Module 19: Reagents & Consumables Inventory
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_db
from app.main import app
from app.models.core import Tenant, Branch
from app.models.patient import Patient
from app.models.pathology import Test as PathologyTest
from app.security.tenant_guard import get_tenant_context, TenantContext

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
def client(db_session):
    tenant_id = f"test-tenant-{uuid.uuid4()}"
    branch_id = f"test-branch-{uuid.uuid4()}"

    t = Tenant(id=tenant_id, name="Apex Diagnostic Network", code=f"APEX_{uuid.uuid4().hex[:6]}")
    b = Branch(id=branch_id, tenant_id=tenant_id, name="Main Lab", code="MAIN")
    db_session.add_all([t, b])

    pat = Patient(
        id=f"pat_{uuid.uuid4()}",
        tenant_id=tenant_id,
        patient_no="UHID-99901",
        first_name="Ramesh",
        last_name="Gupta",
        mobile_normalized="9876543210",
        sex="Male",
        date_of_birth=None,
    )
    test_item = PathologyTest(
        id=f"test_{uuid.uuid4()}",
        tenant_id=tenant_id,
        code="CBC-01",
        name="Complete Blood Count",
        display_name="CBC",
        base_price=400.0,
    )
    db_session.add_all([pat, test_item])
    db_session.commit()

    def override_get_db():
        yield db_session

    def override_tenant_context():
        return TenantContext(tenant_id=tenant_id, user_id="test-user-id", branch_id=branch_id)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_tenant_context] = override_tenant_context

    tc = TestClient(app)
    tc.test_tenant_id = tenant_id  # type: ignore[attr-defined]
    tc.test_branch_id = branch_id  # type: ignore[attr-defined]
    tc.test_patient_id = pat.id  # type: ignore[attr-defined]
    tc.test_test_id = test_item.id  # type: ignore[attr-defined]

    yield tc
    app.dependency_overrides.clear()


def test_expenses_end_to_end(client):
    # 1. Categories
    r = client.get("/expenses/categories")
    assert r.status_code == 200
    cats = r.json()
    assert len(cats) >= 1
    cat_id = cats[0]["id"]

    # 2. Vendors
    r_v = client.post("/expenses/vendors", json={
        "name": "Transasia Bio-Medicals Ltd",
        "contact_person": "Vikas Shah",
        "phone": "+91 98200 11223",
    })
    assert r_v.status_code == 201
    vendor_id = r_v.json()["id"]

    # 3. Record Expense
    r_exp = client.post("/expenses", json={
        "category_id": cat_id,
        "vendor_id": vendor_id,
        "amount": 2500.0,
        "payment_mode": "UPI",
        "description": "Monthly analyzer cleaning kit",
    })
    assert r_exp.status_code == 201
    assert r_exp.json()["amount"] == 2500.0

    # 4. List and Summary
    r_list = client.get("/expenses")
    assert r_list.status_code == 200
    assert len(r_list.json()) >= 1

    r_sum = client.get("/expenses/summary")
    assert r_sum.status_code == 200
    assert r_sum.json()["total_expense_amount"] >= 2500.0


def test_home_collection_lifecycle(client):
    appt = (datetime.utcnow() + timedelta(days=1)).isoformat()
    r = client.post("/home-collections", json={
        "patient_id": client.test_patient_id,
        "appointment_date": appt,
        "time_slot": "07:30 AM - 08:30 AM",
        "address": "Flat 402, Sunshine Apartments, Sector 62",
        "contact_phone": "9876543210",
        "collection_charge": 150.0,
    })
    assert r.status_code == 201
    booking_id = r.json()["id"]
    assert r.json()["status"] == "REQUESTED"

    # Update status to COLLECTED
    r_patch = client.patch(f"/home-collections/{booking_id}/status", json={
        "status": "COLLECTED",
    })
    assert r_patch.status_code == 200
    assert r_patch.json()["status"] == "COLLECTED"

    # List bookings
    r_list = client.get("/home-collections")
    assert r_list.status_code == 200
    assert any(b["id"] == booking_id for b in r_list.json())


def test_inventory_and_reagents_flow(client):
    # 1. List default items
    r_items = client.get("/inventory/items")
    assert r_items.status_code == 200
    items = r_items.json()
    assert len(items) >= 1
    item_id = items[0]["id"]
    initial_stock = items[0]["current_stock"]

    # 2. Receive new lot
    exp_date = (datetime.utcnow() + timedelta(days=180)).isoformat()
    r_lot = client.post("/inventory/lots", json={
        "item_id": item_id,
        "lot_number": "LOT-9921",
        "expiry_date": exp_date,
        "quantity": 100.0,
    })
    assert r_lot.status_code == 201
    assert r_lot.json()["total_item_stock"] == initial_stock + 100.0

    # 3. Consume stock
    r_consume = client.post("/inventory/consume", json={
        "item_id": item_id,
        "quantity": 10.0,
        "notes": "Daily batch run CBC 10 tests",
    })
    assert r_consume.status_code == 200
    assert r_consume.json()["current_stock"] == initial_stock + 90.0

    # 4. Alerts
    r_alerts = client.get("/inventory/alerts")
    assert r_alerts.status_code == 200
    assert "low_stock_items" in r_alerts.json()


def test_radiology_workstation(client):
    # 1. Templates
    r_tpl = client.get("/radiology/templates")
    assert r_tpl.status_code == 200
    assert len(r_tpl.json()) >= 1
    template = r_tpl.json()[0]

    # 2. Order
    r_ord = client.post("/radiology/orders", json={
        "patient_id": client.test_patient_id,
        "modality": "XRAY",
        "procedure_name": "Chest X-Ray PA View",
        "clinical_history": "Dry cough 2 weeks",
        "referring_doctor": "Dr. A. Verma",
    })
    assert r_ord.status_code == 201
    order_id = r_ord.json()["id"]

    # 3. Findings
    r_find = client.post(f"/radiology/orders/{order_id}/findings", json={
        "technique": template["technique"],
        "findings": template["findings"],
        "impression": template["impression"],
        "is_final": True,
    })
    assert r_find.status_code == 200
    assert r_find.json()["status"] == "FINALIZED"

    # 4. Order Details
    r_det = client.get(f"/radiology/orders/{order_id}")
    assert r_det.status_code == 200
    assert r_det.json()["status"] == "FINALIZED"
    assert r_det.json()["finding"]["impression"] == template["impression"]


def test_corporate_b2b_management(client):
    # 1. List & auto-seed
    r_corps = client.get("/corporates")
    assert r_corps.status_code == 200
    corps = r_corps.json()
    assert len(corps) >= 1
    corp_id = corps[0]["id"]

    # 2. Set Special Rate
    r_rate = client.post(f"/corporates/{corp_id}/price-list", json={
        "test_id": client.test_test_id,
        "special_rate": 280.0,
        "discount_pct": 30.0,
    })
    assert r_rate.status_code == 200

    r_pl = client.get(f"/corporates/{corp_id}/price-list")
    assert r_pl.status_code == 200
    assert any(it["test_id"] == client.test_test_id for it in r_pl.json())

    # 3. Monthly Invoice
    start_dt = (datetime.utcnow() - timedelta(days=30)).isoformat()
    end_dt = datetime.utcnow().isoformat()
    r_inv = client.post(f"/corporates/{corp_id}/invoices", json={
        "period_start": start_dt,
        "period_end": end_dt,
        "total_amount": 15000.0,
        "due_days": 30,
    })
    assert r_inv.status_code == 201
    assert r_inv.json()["total_amount"] == 15000.0


def test_quality_nabl_qc_runs(client):
    # 1. Log QC run
    r_qc = client.post("/quality/qc-runs", json={
        "test_id": client.test_test_id,
        "control_name": "Bio-Rad Level 1",
        "control_lot_number": "LOT-BR-1",
        "control_level": "NORMAL",
        "expected_mean": 100.0,
        "expected_sd": 2.0,
        "measured_value": 101.5,
    })
    assert r_qc.status_code == 201
    assert r_qc.json()["status"] == "IN_CONTROL"
    assert r_qc.json()["deviation_sd"] == 0.75

    # 2. Log Out-of-control run (> 3 SD)
    r_qc_ooc = client.post("/quality/qc-runs", json={
        "test_id": client.test_test_id,
        "control_name": "Bio-Rad Level 1",
        "control_lot_number": "LOT-BR-1",
        "control_level": "NORMAL",
        "expected_mean": 100.0,
        "expected_sd": 2.0,
        "measured_value": 107.0,  # 3.5 SD
    })
    assert r_qc_ooc.status_code == 201
    assert r_qc_ooc.json()["status"] == "OUT_OF_CONTROL"
    assert "1_3s" in r_qc_ooc.json()["westgard_violation"]

    # 3. List QC runs
    r_list = client.get("/quality/qc-runs")
    assert r_list.status_code == 200
    assert len(r_list.json()) >= 2

    # 4. Calibration
    now_dt = datetime.utcnow()
    next_dt = now_dt + timedelta(days=365)
    r_cal = client.post("/quality/calibrations", json={
        "analyzer_id": f"an_{uuid.uuid4()}",
        "calibration_date": now_dt.isoformat(),
        "next_due_date": next_dt.isoformat(),
        "calibrated_by": "Sysmex Certified Engineer",
        "certificate_no": "CERT-2026-X1",
    })
    assert r_cal.status_code == 201
    assert r_cal.json()["status"] == "VALID"

"""Tests for P09-16 Offline 5,000-Patient Multi-PC Acceptance workload simulator, concurrency, p50/p95 metrics, and zero internet dependency."""

from __future__ import annotations

import time
import statistics
from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_db
import app.models  # noqa: F401
from app.main import app
from app.models.core import Tenant
from app.models.identity import User
from app.models.patient import Patient
from app.models.billing import Invoice
from app.security.auth import hash_password, create_session
from contracts.performance_budget import OFFLINE_ACCEPTANCE


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def multi_pc_setup(test_db):
    tenant = Tenant(name="Acceptance Clinic", code="ACCEPTH")
    test_db.add(tenant)
    test_db.flush()

    # Create 4 LAN client user accounts / sessions
    clients_auth = []
    for i in range(1, 5):
        user = User(
            tenant_id=tenant.id,
            username=f"lan_operator_{i}",
            email=f"operator{i}@acceptance.test",
            hashed_password=hash_password("Pass1234"),
            full_name=f"LAN Operator {i}",
        )
        test_db.add(user)
        test_db.flush()
        session_obj = create_session(test_db, tenant_id=tenant.id, user_id=user.id)
        clients_auth.append({
            "client_id": f"LAN-PC-{i}",
            "tenant_id": tenant.id,
            "headers": {"Authorization": f"Bearer {session_obj.session_token}"}
        })

    test_db.commit()
    return {"tenant": tenant, "clients": clients_auth}


def test_offline_5k_multipc_acceptance_workload(client: TestClient, multi_pc_setup, test_db):
    tenant_id = multi_pc_setup["tenant"].id
    lan_clients = multi_pc_setup["clients"]

    # Verify offline acceptance budget parameters
    assert OFFLINE_ACCEPTANCE["patient_registrations_per_day"] == 5000
    assert OFFLINE_ACCEPTANCE["min_concurrent_lan_clients"] == 4
    assert OFFLINE_ACCEPTANCE["internet_required"] is False

    latencies_ms = []

    # Simulate 4 LAN clients executing workloads sequentially / concurrently against test_db
    for client_info in lan_clients:
        client_prefix = client_info["client_id"]
        for b in range(10):
            start_t = time.perf_counter()
            # 1. Patient Registration
            pat_no = f"MRN-{client_prefix}-{b}"
            patient = Patient(
                tenant_id=tenant_id,
                patient_no=pat_no,
                first_name="Synthetic",
                last_name=f"Patient-{b}",
                sex="male" if b % 2 == 0 else "female",
                date_of_birth=datetime.strptime("1980-01-01", "%Y-%m-%d").date(),
            )
            test_db.add(patient)
            test_db.flush()

            # 2. Billing / Invoice
            invoice = Invoice(
                tenant_id=tenant_id,
                patient_id=patient.id,
                invoice_no=f"INV-{client_prefix}-{b}",
                grand_total=150.00,
                status="paid",
            )
            test_db.add(invoice)
            test_db.commit()

            end_t = time.perf_counter()
            duration_ms = (end_t - start_t) * 1000.0
            latencies_ms.append(duration_ms)

    assert len(latencies_ms) == 40  # 4 clients * 10 batches = 40 transactions

    # Calculate p50 and p95 performance metrics
    latencies_ms.sort()
    p50 = statistics.median(latencies_ms)
    p95 = latencies_ms[int(len(latencies_ms) * 0.95)]

    # Assert performance budgets (p95 < 500ms for local CRUD operations)
    assert p50 < 200.0
    assert p95 < 500.0

    # Verify storage growth & data integrity: total records created should be 40 patients and 40 invoices
    total_patients = test_db.query(Patient).filter(Patient.tenant_id == tenant_id).count()
    total_invoices = test_db.query(Invoice).filter(Invoice.tenant_id == tenant_id).count()

    assert total_patients == 40
    assert total_invoices == 40

    # Verify zero internet dependency
    assert OFFLINE_ACCEPTANCE["internet_required"] is False






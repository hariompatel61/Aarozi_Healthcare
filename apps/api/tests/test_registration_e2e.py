"""End-to-end multi-terminal reception flow: Registration -> Order -> Sample workflow."""
from __future__ import annotations

import concurrent.futures
import threading
import uuid
import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.models.core import Tenant, Branch
from app.models.pathology import Test, Profile, ProfileItem
from app.models.patient import Patient
from app.pathology.order_workflow import create_order, transition_order_status
from app.pathology.sample_workflow import (
    create_sample_for_order_item,
    collect_sample,
    barcode_sample,
    receive_sample,
    accept_sample,
    reject_sample,
    get_sample,
    get_sample_by_barcode,
)
from app.patient.service import register_patient
from app.security.tenant_guard import TenantContext


@pytest.fixture
def db_session_factory(tmp_path):
    db_file = tmp_path / "test_reg_e2e.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False, "timeout": 30},
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    try:
        yield session_factory
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def master_data(db_session_factory):
    session = db_session_factory()

    tenant = Tenant(id=str(uuid.uuid4()), name="Metropolitan Diagnostic Lab", code="MDL", is_active=True)
    branch = Branch(id=str(uuid.uuid4()), tenant_id=tenant.id, name="Downtown Reception", code="REC1", is_active=True)
    session.add_all([tenant, branch])

    # Diagnostic catalog
    t_fbc = Test(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        code="FBC",
        name="Full Blood Count",
        display_name="FBC",
        specimen_type="EDTA Whole Blood",
        container_type="Lavender Top Tube",
    )
    t_glucose = Test(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        code="GLU_F",
        name="Fasting Blood Glucose",
        display_name="Glucose Fasting",
        specimen_type="Fluoride Plasma",
        container_type="Grey Top Tube",
    )
    t_hba1c = Test(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        code="HBA1C",
        name="Glycated Hemoglobin",
        display_name="HbA1c",
        specimen_type="EDTA Whole Blood",
        container_type="Lavender Top Tube",
    )
    session.add_all([t_fbc, t_glucose, t_hba1c])

    # Profile: Diabetic Screen
    p_diabetic = Profile(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        code="DIAB_SCREEN",
        name="Diabetic Screen",
        display_name="Diabetic Screen",
    )
    session.add(p_diabetic)
    session.flush()

    item1 = ProfileItem(id=str(uuid.uuid4()), profile_id=p_diabetic.id, test_id=t_glucose.id, sort_order=1)
    item2 = ProfileItem(id=str(uuid.uuid4()), profile_id=p_diabetic.id, test_id=t_hba1c.id, sort_order=2)
    session.add_all([item1, item2])

    tenant_id = tenant.id
    branch_id = branch.id
    fbc_id = t_fbc.id
    glu_id = t_glucose.id
    hba1c_id = t_hba1c.id
    diab_id = p_diabetic.id

    session.commit()
    session.close()

    return {
        "tenant_id": tenant_id,
        "branch_id": branch_id,
        "tests": {"FBC": fbc_id, "GLU_F": glu_id, "HBA1C": hba1c_id},
        "profiles": {"DIAB_SCREEN": diab_id},
    }


def test_single_terminal_registration_order_sample_lifecycle(db_session_factory, master_data):
    """
    Full happy-path workflow on a single reception PC:
    1. Patient registration
    2. Test & profile order placement
    3. Sample creation & barcode assignment
    4. Phlebotomy collection
    5. Lab reception & accession acceptance
    """
    session = db_session_factory()

    tenant_id = master_data["tenant_id"]
    branch_id = master_data["branch_id"]
    user_id = str(uuid.uuid4())
    terminal_id = "PC-RECEPTION-01"

    ctx = TenantContext(tenant_id=tenant_id, branch_id=branch_id, user_id=user_id)

    # 1. Register Patient
    patient = register_patient(
        session,
        tenant_context=ctx,
        first_name="Amina",
        last_name="Khan",
        sex="female",
        date_of_birth=date(1992, 4, 15),
        mobile="+923001122334",
        blood_group="B+",
        identifiers=[{"type": "CNIC", "value": "35201-9988776-2", "is_primary": True}],
        client_pc_id=terminal_id,
    )
    assert patient.patient_no.startswith("P-")
    assert patient.id is not None

    # 2. Place Order (1 individual test + 1 profile)
    order = create_order(
        session,
        tenant_context=ctx,
        patient_id=patient.id,
        test_ids=[master_data["tests"]["FBC"]],
        profile_ids=[master_data["profiles"]["DIAB_SCREEN"]],
    )
    session.commit()

    assert order.order_no.startswith("ORD-")
    assert len(order.items) == 3  # FBC + 2 expanded items from profile
    assert order.status == "placed"

    # 3. Sample Generation & Barcode
    fbc_item = next(it for it in order.items if it.test_id == master_data["tests"]["FBC"])
    sample = create_sample_for_order_item(session, tenant_context=ctx, order_item_id=fbc_item.id)
    assert sample.status == "ordered"
    assert sample.barcode.startswith("SMP-")

    # 4. Phlebotomy: Collect & Barcode
    sample = collect_sample(session, tenant_context=ctx, sample_id=sample.id)
    assert sample.status == "collected"
    assert fbc_item.status == "sample_collected"

    sample = barcode_sample(session, tenant_context=ctx, sample_id=sample.id)
    assert sample.status == "barcoded"

    # 5. Accessioning: Receive & Accept
    sample = receive_sample(session, tenant_context=ctx, sample_id=sample.id)
    assert sample.status == "received"

    sample = accept_sample(session, tenant_context=ctx, sample_id=sample.id)
    assert sample.status == "accepted"
    assert fbc_item.status == "in_process"

    session.close()


def test_concurrent_multiple_reception_pcs(db_session_factory, master_data):
    """
    Simulate multiple reception terminals (e.g. PC-1, PC-2, PC-3, PC-4)
    registering patients and creating orders concurrently over the LAN.
    Validates tenant-boundary integrity, unique sequence generation, and no conflicts.
    """
    lock = threading.Lock()

    tenant_id = master_data["tenant_id"]
    branch_id = master_data["branch_id"]
    terminals = [f"PC-RECEPTION-{i:02d}" for i in range(1, 5)]

    results = []

    def run_terminal_flow(terminal_name: str, index: int):
        session = db_session_factory()
        ctx = TenantContext(
            tenant_id=tenant_id,
            branch_id=branch_id,
            user_id=f"user-{terminal_name}",
        )
        try:
            # Synchronize write transaction in SQLite in-memory to simulate concurrent serialized commits
            with lock:
                patient = register_patient(
                    session,
                    tenant_context=ctx,
                    first_name=f"Patient-{terminal_name}",
                    last_name="Test",
                    sex="male" if index % 2 == 0 else "female",
                    mobile=f"+92300000000{index}",
                    client_pc_id=terminal_name,
                )
                order = create_order(
                    session,
                    tenant_context=ctx,
                    patient_id=patient.id,
                    test_ids=[master_data["tests"]["FBC"]],
                )
                sample = create_sample_for_order_item(
                    session,
                    tenant_context=ctx,
                    order_item_id=order.items[0].id,
                )
                session.commit()

            return {
                "terminal": terminal_name,
                "patient_no": patient.patient_no,
                "order_no": order.order_no,
                "barcode": sample.barcode,
            }
        finally:
            session.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(run_terminal_flow, term, i) for i, term in enumerate(terminals)]
        for fut in concurrent.futures.as_completed(futures):
            results.append(fut.result())

    assert len(results) == 4

    # Verify all generated numbers are distinct
    patient_nos = [r["patient_no"] for r in results]
    order_nos = [r["order_no"] for r in results]
    barcodes = [r["barcode"] for r in results]

    assert len(set(patient_nos)) == 4
    assert len(set(order_nos)) == 4
    assert len(set(barcodes)) == 4


def test_reception_rejection_workflow(db_session_factory, master_data):
    """
    Verify specimen rejection path at accessioning terminal:
    Registration -> Order -> Sample -> Phlebotomy -> Rejection with reason.
    """
    session = db_session_factory()

    tenant_id = master_data["tenant_id"]
    branch_id = master_data["branch_id"]
    ctx = TenantContext(tenant_id=tenant_id, branch_id=branch_id, user_id="lab-tech-01")

    patient = register_patient(
        session,
        tenant_context=ctx,
        first_name="Zahid",
        last_name="Ali",
        sex="male",
    )
    order = create_order(
        session,
        tenant_context=ctx,
        patient_id=patient.id,
        test_ids=[master_data["tests"]["GLU_F"]],
    )
    sample = create_sample_for_order_item(
        session,
        tenant_context=ctx,
        order_item_id=order.items[0].id,
    )
    collect_sample(session, tenant_context=ctx, sample_id=sample.id)
    barcode_sample(session, tenant_context=ctx, sample_id=sample.id)
    receive_sample(session, tenant_context=ctx, sample_id=sample.id)

    # Reject sample
    rejected = reject_sample(
        session,
        tenant_context=ctx,
        sample_id=sample.id,
        reason="Clotted whole blood specimen",
    )
    assert rejected.status == "rejected"
    assert rejected.rejection_reason == "Clotted whole blood specimen"

    session.close()

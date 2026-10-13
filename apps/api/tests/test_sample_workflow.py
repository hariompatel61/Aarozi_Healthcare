from __future__ import annotations

import uuid
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.models.core import Tenant, Branch
from app.security.tenant_guard import TenantContext
from app.models.patient import Patient
from app.models.pathology import Test, Order, OrderItem, Sample
from app.pathology.order_workflow import create_order
from app.pathology.sample_workflow import (
    create_sample_for_order_item,
    collect_sample,
    barcode_sample,
    receive_sample,
    accept_sample,
    reject_sample,
    advance_sample_status,
    get_sample,
    get_sample_by_barcode,
    list_samples,
    SampleNotFoundError,
    SampleStateTransitionError,
    InvalidSampleInputError,
    generate_sample_barcode,
)


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


@pytest.fixture
def sample_test_setup(db_session: Session):
    tenant = Tenant(id=str(uuid.uuid4()), name="Pathology Lab 1", code="PL1", is_active=True)
    branch = Branch(id=str(uuid.uuid4()), tenant_id=tenant.id, name="Main Branch", code="MB1")
    db_session.add_all([tenant, branch])

    patient = Patient(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        branch_id=branch.id,
        patient_no="P-009999",
        first_name="John",
        last_name="Doe",
        sex="male",
    )
    db_session.add(patient)

    t1 = Test(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        code="CBC",
        name="Complete Blood Count",
        display_name="CBC",
        specimen_type="EDTA Whole Blood",
        container_type="Lavender Top Tube",
    )
    t2 = Test(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        code="LIPID",
        name="Lipid Profile",
        display_name="Lipid",
        specimen_type="Serum",
        container_type="Gold SST",
    )
    db_session.add_all([t1, t2])
    db_session.commit()

    ctx = TenantContext(tenant_id=tenant.id, branch_id=branch.id, user_id=str(uuid.uuid4()))
    order = create_order(
        db_session,
        tenant_context=ctx,
        patient_id=patient.id,
        test_ids=[t1.id, t2.id],
    )

    return {
        "tenant": tenant,
        "branch": branch,
        "patient": patient,
        "tests": {"CBC": t1, "LIPID": t2},
        "order": order,
        "ctx": ctx,
    }


def test_create_and_barcode_sample(db_session: Session, sample_test_setup):
    ctx = sample_test_setup["ctx"]
    order = sample_test_setup["order"]
    item = order.items[0]

    sample = create_sample_for_order_item(
        db_session,
        tenant_context=ctx,
        order_item_id=item.id,
    )

    assert sample.id is not None
    assert sample.barcode.startswith("SMP-")
    assert sample.specimen_type == "EDTA Whole Blood"
    assert sample.container_type == "Lavender Top Tube"
    assert sample.status == "ordered"

    # Lookup by barcode
    found = get_sample_by_barcode(db_session, tenant_context=ctx, barcode=sample.barcode)
    assert found.id == sample.id


def test_sample_state_machine_happy_path(db_session: Session, sample_test_setup):
    ctx = sample_test_setup["ctx"]
    order = sample_test_setup["order"]
    item = order.items[0]

    sample = create_sample_for_order_item(db_session, tenant_context=ctx, order_item_id=item.id)

    # 1. ORDERED -> COLLECTED
    sample = collect_sample(db_session, tenant_context=ctx, sample_id=sample.id)
    assert sample.status == "collected"
    assert sample.collected_at is not None
    assert sample.collected_by == ctx.user_id
    assert item.status == "sample_collected"
    assert order.status == "sample_collected"

    # 2. COLLECTED -> BARCODED
    sample = barcode_sample(db_session, tenant_context=ctx, sample_id=sample.id)
    assert sample.status == "barcoded"

    # 3. BARCODED -> RECEIVED
    sample = receive_sample(db_session, tenant_context=ctx, sample_id=sample.id)
    assert sample.status == "received"
    assert sample.received_at is not None
    assert sample.received_by == ctx.user_id

    # 4. RECEIVED -> ACCEPTED
    sample = accept_sample(db_session, tenant_context=ctx, sample_id=sample.id)
    assert sample.status == "accepted"
    assert sample.accepted_at is not None
    assert item.status == "in_process"
    assert order.status == "in_process"

    # 5. ACCEPTED -> IN_PROCESS
    sample = advance_sample_status(db_session, tenant_context=ctx, sample_id=sample.id, target_status="in_process")
    assert sample.status == "in_process"

    # 6. IN_PROCESS -> RESULT_READY
    sample = advance_sample_status(db_session, tenant_context=ctx, sample_id=sample.id, target_status="result_ready")
    assert sample.status == "result_ready"


def test_sample_rejection_requires_reason(db_session: Session, sample_test_setup):
    ctx = sample_test_setup["ctx"]
    order = sample_test_setup["order"]
    item = order.items[0]

    sample = create_sample_for_order_item(db_session, tenant_context=ctx, order_item_id=item.id)
    collect_sample(db_session, tenant_context=ctx, sample_id=sample.id)
    barcode_sample(db_session, tenant_context=ctx, sample_id=sample.id)
    receive_sample(db_session, tenant_context=ctx, sample_id=sample.id)

    # Rejection without reason fails
    with pytest.raises(SampleStateTransitionError, match="mandatory"):
        reject_sample(db_session, tenant_context=ctx, sample_id=sample.id, reason="")

    # Rejection with reason succeeds
    sample = reject_sample(
        db_session,
        tenant_context=ctx,
        sample_id=sample.id,
        reason="Hemolyzed specimen",
    )
    assert sample.status == "rejected"
    assert sample.rejection_reason == "Hemolyzed specimen"
    assert sample.rejected_at is not None
    assert sample.rejected_by == ctx.user_id


def test_invalid_state_transitions(db_session: Session, sample_test_setup):
    ctx = sample_test_setup["ctx"]
    order = sample_test_setup["order"]
    item = order.items[0]

    sample = create_sample_for_order_item(db_session, tenant_context=ctx, order_item_id=item.id)

    # Cannot skip from ORDERED directly to RECEIVED or ACCEPTED
    with pytest.raises(SampleStateTransitionError):
        receive_sample(db_session, tenant_context=ctx, sample_id=sample.id)

    with pytest.raises(SampleStateTransitionError):
        accept_sample(db_session, tenant_context=ctx, sample_id=sample.id)

    with pytest.raises(SampleStateTransitionError):
        reject_sample(db_session, tenant_context=ctx, sample_id=sample.id, reason="Invalid step")


def test_tenant_isolation_in_samples(db_session: Session, sample_test_setup):
    ctx = sample_test_setup["ctx"]
    order = sample_test_setup["order"]
    item = order.items[0]

    sample = create_sample_for_order_item(db_session, tenant_context=ctx, order_item_id=item.id)

    other_tenant = Tenant(id=str(uuid.uuid4()), name="Other Facility", code="OF1", is_active=True)
    db_session.add(other_tenant)
    db_session.commit()

    other_ctx = TenantContext(tenant_id=other_tenant.id, branch_id=None, user_id="other-user")

    # Cannot get other tenant's sample
    with pytest.raises(SampleNotFoundError):
        get_sample(db_session, tenant_context=other_ctx, sample_id=sample.id)

    # Cannot get other tenant's sample by barcode
    with pytest.raises(SampleNotFoundError):
        get_sample_by_barcode(db_session, tenant_context=other_ctx, barcode=sample.barcode)

    # List samples returns none for other tenant
    other_samples = list_samples(db_session, tenant_context=other_ctx)
    assert len(other_samples) == 0

    # Cannot transition other tenant's sample
    with pytest.raises(SampleNotFoundError):
        collect_sample(db_session, tenant_context=other_ctx, sample_id=sample.id)


def test_list_samples_filtering(db_session: Session, sample_test_setup):
    ctx = sample_test_setup["ctx"]
    order = sample_test_setup["order"]
    item1 = order.items[0]
    item2 = order.items[1]

    s1 = create_sample_for_order_item(db_session, tenant_context=ctx, order_item_id=item1.id)
    s2 = create_sample_for_order_item(db_session, tenant_context=ctx, order_item_id=item2.id)

    collect_sample(db_session, tenant_context=ctx, sample_id=s1.id)

    all_samples = list_samples(db_session, tenant_context=ctx)
    assert len(all_samples) == 2

    collected = list_samples(db_session, tenant_context=ctx, status="collected")
    assert len(collected) == 1
    assert collected[0].id == s1.id

    ordered = list_samples(db_session, tenant_context=ctx, status="ordered")
    assert len(ordered) == 1
    assert ordered[0].id == s2.id

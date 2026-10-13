from __future__ import annotations

import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.models.core import Tenant, Branch
from app.security.tenant_guard import TenantContext
from app.models.patient import Patient
from app.models.pathology import Test, Profile, ProfileItem, Package, PackageItem, Order, OrderItem
from app.pathology.order_workflow import (
    create_order,
    get_order,
    list_orders,
    transition_order_status,
    transition_order_item_status,
    OrderNotFoundError,
    OrderStateTransitionError,
    PatientNotFoundError,
    InvalidOrderInputError,
    generate_order_no,
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
def test_setup(db_session: Session):
    tenant = Tenant(id=str(uuid.uuid4()), name="Apex Pathology", code="APEX", is_active=True)
    branch = Branch(id=str(uuid.uuid4()), tenant_id=tenant.id, name="Apex Central", code="AC1")
    db_session.add_all([tenant, branch])

    patient = Patient(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        branch_id=branch.id,
        patient_no="P-001001",
        first_name="Sarah",
        last_name="Connor",
        sex="female",
    )
    db_session.add(patient)

    t1 = Test(id=str(uuid.uuid4()), tenant_id=tenant.id, code="GLU", name="Glucose Fasting", display_name="Fasting Blood Sugar")
    t2 = Test(id=str(uuid.uuid4()), tenant_id=tenant.id, code="CHOL", name="Total Cholesterol", display_name="Cholesterol")
    t3 = Test(id=str(uuid.uuid4()), tenant_id=tenant.id, code="HDL", name="HDL Cholesterol", display_name="HDL")
    db_session.add_all([t1, t2, t3])

    prof = Profile(id=str(uuid.uuid4()), tenant_id=tenant.id, code="LIPID", name="Lipid Panel", display_name="Lipid Panel")
    db_session.add(prof)
    db_session.flush()

    pi1 = ProfileItem(profile_id=prof.id, test_id=t2.id, sort_order=1)
    pi2 = ProfileItem(profile_id=prof.id, test_id=t3.id, sort_order=2)
    db_session.add_all([pi1, pi2])

    pkg = Package(id=str(uuid.uuid4()), tenant_id=tenant.id, code="HEALTH_BASIC", name="Basic Health Checkup", display_name="Basic Health")
    db_session.add(pkg)
    db_session.flush()

    pki1 = PackageItem(package_id=pkg.id, test_id=t1.id, sort_order=1)
    pki2 = PackageItem(package_id=pkg.id, profile_id=prof.id, sort_order=2)
    db_session.add_all([pki1, pki2])

    db_session.commit()

    ctx = TenantContext(tenant_id=tenant.id, branch_id=branch.id, user_id=str(uuid.uuid4()))
    return {
        "tenant": tenant,
        "branch": branch,
        "patient": patient,
        "tests": {"GLU": t1, "CHOL": t2, "HDL": t3},
        "profile": prof,
        "package": pkg,
        "ctx": ctx,
    }


def test_create_order_with_expanded_items(db_session: Session, test_setup):
    ctx = test_setup["ctx"]
    patient = test_setup["patient"]
    t_glu = test_setup["tests"]["GLU"]
    prof = test_setup["profile"]

    order = create_order(
        db_session,
        tenant_context=ctx,
        patient_id=patient.id,
        test_ids=[t_glu.id],
        profile_ids=[prof.id],
    )

    assert order.id is not None
    assert order.order_no.startswith("ORD-")
    assert order.status == "placed"
    assert len(order.items) == 3

    fetched = get_order(db_session, tenant_context=ctx, order_id=order.id)
    assert fetched.order_no == order.order_no
    assert len(fetched.items) == 3


def test_create_order_with_package(db_session: Session, test_setup):
    ctx = test_setup["ctx"]
    patient = test_setup["patient"]
    pkg = test_setup["package"]

    order = create_order(
        db_session,
        tenant_context=ctx,
        patient_id=patient.id,
        package_ids=[pkg.id],
    )

    assert order.id is not None
    assert len(order.items) == 3
    # Check that package names and profile names are populated on items
    package_names = [it.package_name for it in order.items]
    assert all(name == "Basic Health Checkup" for name in package_names)


def test_order_state_transitions(db_session: Session, test_setup):
    ctx = test_setup["ctx"]
    patient = test_setup["patient"]
    t_glu = test_setup["tests"]["GLU"]

    order = create_order(
        db_session,
        tenant_context=ctx,
        patient_id=patient.id,
        test_ids=[t_glu.id],
        initial_status="placed",
    )

    # Transition to sample_collected
    transition_order_status(db_session, tenant_context=ctx, order_id=order.id, target_status="sample_collected")
    assert order.status == "sample_collected"
    assert order.items[0].status == "sample_collected"

    # Transition to in_process
    transition_order_status(db_session, tenant_context=ctx, order_id=order.id, target_status="in_process")
    assert order.status == "in_process"

    # Transition to completed
    transition_order_status(db_session, tenant_context=ctx, order_id=order.id, target_status="completed")
    assert order.status == "completed"

    # Transition from completed to cancelled is not allowed
    with pytest.raises(OrderStateTransitionError):
        transition_order_status(
            db_session,
            tenant_context=ctx,
            order_id=order.id,
            target_status="cancelled",
            reason="Test",
        )


def test_order_cancellation_requires_reason(db_session: Session, test_setup):
    ctx = test_setup["ctx"]
    patient = test_setup["patient"]
    t_glu = test_setup["tests"]["GLU"]

    order = create_order(
        db_session,
        tenant_context=ctx,
        patient_id=patient.id,
        test_ids=[t_glu.id],
    )

    with pytest.raises(OrderStateTransitionError, match="Cancellation reason is required"):
        transition_order_status(db_session, tenant_context=ctx, order_id=order.id, target_status="cancelled", reason="")

    transition_order_status(
        db_session,
        tenant_context=ctx,
        order_id=order.id,
        target_status="cancelled",
        reason="Patient requested cancellation",
    )
    assert order.status == "cancelled"
    assert order.cancellation_reason == "Patient requested cancellation"
    assert order.cancelled_by == ctx.user_id
    assert order.items[0].status == "cancelled"


def test_item_level_transition_and_order_aggregation(db_session: Session, test_setup):
    ctx = test_setup["ctx"]
    patient = test_setup["patient"]
    prof = test_setup["profile"]

    order = create_order(
        db_session,
        tenant_context=ctx,
        patient_id=patient.id,
        profile_ids=[prof.id],
    )
    assert len(order.items) == 2

    # Transition order to in_process
    transition_order_status(db_session, tenant_context=ctx, order_id=order.id, target_status="in_process")

    item1, item2 = order.items[0], order.items[1]

    # Complete item1 -> order should be partial_completed
    transition_order_item_status(
        db_session,
        tenant_context=ctx,
        order_id=order.id,
        order_item_id=item1.id,
        target_status="completed",
    )
    assert item1.status == "completed"
    assert order.status == "partial_completed"

    # Complete item2 -> order should be completed
    transition_order_item_status(
        db_session,
        tenant_context=ctx,
        order_id=order.id,
        order_item_id=item2.id,
        target_status="completed",
    )
    assert item2.status == "completed"
    assert order.status == "completed"


def test_multi_tenant_isolation_in_orders(db_session: Session, test_setup):
    ctx = test_setup["ctx"]
    patient = test_setup["patient"]
    t_glu = test_setup["tests"]["GLU"]

    order = create_order(
        db_session,
        tenant_context=ctx,
        patient_id=patient.id,
        test_ids=[t_glu.id],
    )

    other_tenant = Tenant(id=str(uuid.uuid4()), name="Other Clinic", code="OCL", is_active=True)
    db_session.add(other_tenant)
    db_session.commit()

    other_ctx = TenantContext(tenant_id=other_tenant.id, branch_id=None, user_id="other-user")

    # Other tenant cannot get order
    with pytest.raises(OrderNotFoundError):
        get_order(db_session, tenant_context=other_ctx, order_id=order.id)

    # Other tenant cannot list this order
    orders = list_orders(db_session, tenant_context=other_ctx)
    assert len(orders) == 0

    # Other tenant cannot transition this order
    with pytest.raises(OrderNotFoundError):
        transition_order_status(db_session, tenant_context=other_ctx, order_id=order.id, target_status="cancelled", reason="Illegal")


def test_invalid_order_inputs(db_session: Session, test_setup):
    ctx = test_setup["ctx"]
    patient = test_setup["patient"]

    # Missing items
    with pytest.raises(InvalidOrderInputError):
        create_order(db_session, tenant_context=ctx, patient_id=patient.id)

    # Non-existent patient
    with pytest.raises(PatientNotFoundError):
        create_order(
            db_session,
            tenant_context=ctx,
            patient_id=str(uuid.uuid4()),
            test_ids=[test_setup["tests"]["GLU"].id],
        )

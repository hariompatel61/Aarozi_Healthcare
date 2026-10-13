"""Tests for P04-04: Payment Engine (collection, receipts, idempotent callbacks, partial/full settlements, RBAC, tenant isolation)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.models.core import Tenant, Branch
from app.models.patient import Patient
from app.models.billing import Invoice, Payment
from app.models.identity import User, Role, UserRole, Permission, RolePermission
from app.security.tenant_guard import TenantContext
from app.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.billing.invoice_service import create_invoice
from app.billing.payment_service import (
    record_payment,
    process_payment_callback,
    generate_receipt,
    get_payment,
    list_payments,
    generate_receipt_no,
)
from app.audit.service import get_audit_logs


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


def _setup_payment_env(db_session: Session):
    tenant = Tenant(id=str(uuid.uuid4()), name="Metropolis Health", code="METRO", is_active=True)
    branch = Branch(id=str(uuid.uuid4()), tenant_id=tenant.id, name="Central Branch", code="CBR01")

    patient = Patient(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        patient_no="P-10001",
        first_name="Bruce",
        last_name="Wayne",
        sex="male",
        date_of_birth=datetime(1985, 2, 19).date(),
        mobile_normalized="+1555123456",
        created_at=datetime.now(timezone.utc),
    )

    user = User(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        username="cashier_user",
        email="cashier@example.com",
        hashed_password="fake-hashed-pw",
        full_name="Cashier User",
        is_active=True,
    )

    role = Role(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        name="Billing Staff",
        is_system=False,
    )
    perm = Permission(
        id=str(uuid.uuid4()),
        code="billing.payment",
        module="billing",
        resource="payment",
        action="create",
        risk_level="normal",
    )
    role_perm = RolePermission(role_id=role.id, permission_id=perm.id)
    user_role = UserRole(user_id=user.id, role_id=role.id)

    db_session.add_all([tenant, branch, patient, user, role, perm, role_perm, user_role])
    db_session.flush()

    ctx = TenantContext(
        tenant_id=tenant.id,
        user_id=user.id,
        branch_id=branch.id,
        is_superuser=False,
    )
    return {
        "tenant": tenant,
        "branch": branch,
        "patient": patient,
        "user": user,
        "ctx": ctx,
    }



def test_payment_collection_partial_and_full(db_session: Session):
    env = _setup_payment_env(db_session)

    invoice = create_invoice(
        db_session,
        tenant_context=env["ctx"],
        patient_id=env["patient"].id,
        branch_id=env["branch"].id,
        items=[
            {"description": "MRI Brain", "qty": 1.0, "unit_price": 200.0, "tax_rate_pct": 0.0},
        ],
    )
    assert invoice.grand_total == 200.0
    assert invoice.paid_amount == 0.0
    assert invoice.status == "issued"

    # Part payment
    p1 = record_payment(
        db_session,
        tenant_context=env["ctx"],
        invoice_id=invoice.id,
        amount=80.0,
        method="cash",
    )
    assert p1.amount == 80.0
    assert p1.method == "cash"
    assert p1.receipt_no.startswith("RCP-")
    assert invoice.paid_amount == 80.0
    assert invoice.status == "part_paid"

    # Remaining payment to settle fully
    p2 = record_payment(
        db_session,
        tenant_context=env["ctx"],
        invoice_id=invoice.id,
        amount=120.0,
        method="upi",
        provider_reference="UPI-REF-998877",
    )
    assert p2.amount == 120.0
    assert p2.method == "upi"
    assert invoice.paid_amount == 200.0
    assert invoice.status == "paid"

    # Verify audit trail
    logs = get_audit_logs(db_session, tenant_id=env["tenant"].id, action_code="payment.received")
    assert len(logs) == 2
    assert logs[0].entity_id in {p1.id, p2.id}
    assert logs[1].entity_id in {p1.id, p2.id}


def test_payment_overpayment_rejected(db_session: Session):
    env = _setup_payment_env(db_session)

    invoice = create_invoice(
        db_session,
        tenant_context=env["ctx"],
        patient_id=env["patient"].id,
        branch_id=env["branch"].id,
        items=[
            {"description": "ECG", "qty": 1.0, "unit_price": 50.0},
        ],
    )

    with pytest.raises(ValidationError, match="exceeds balance due"):
        record_payment(
            db_session,
            tenant_context=env["ctx"],
            invoice_id=invoice.id,
            amount=50.01,
            method="cash",
        )

    # Negative or zero amount rejected
    with pytest.raises(ValidationError, match="must be greater than 0"):
        record_payment(
            db_session,
            tenant_context=env["ctx"],
            invoice_id=invoice.id,
            amount=0.0,
            method="cash",
        )


def test_payment_idempotency_key(db_session: Session):
    env = _setup_payment_env(db_session)

    invoice = create_invoice(
        db_session,
        tenant_context=env["ctx"],
        patient_id=env["patient"].id,
        branch_id=env["branch"].id,
        items=[
            {"description": "CBC", "qty": 1.0, "unit_price": 100.0},
        ],
    )

    key = "idem-test-key-12345"
    p1 = record_payment(
        db_session,
        tenant_context=env["ctx"],
        invoice_id=invoice.id,
        amount=50.0,
        method="card",
        idempotency_key=key,
    )
    assert p1.amount == 50.0
    assert invoice.paid_amount == 50.0

    # Repeat payment request with same idempotency key
    p2 = record_payment(
        db_session,
        tenant_context=env["ctx"],
        invoice_id=invoice.id,
        amount=50.0,
        method="card",
        idempotency_key=key,
    )

    assert p1.id == p2.id
    assert invoice.paid_amount == 50.0  # Not double counted
    assert invoice.status == "part_paid"


def test_payment_callback_idempotency(db_session: Session):
    env = _setup_payment_env(db_session)

    invoice = create_invoice(
        db_session,
        tenant_context=env["ctx"],
        patient_id=env["patient"].id,
        branch_id=env["branch"].id,
        items=[
            {"description": "Lipid Profile", "qty": 1.0, "unit_price": 150.0},
        ],
    )

    callback_idem_key = "gateway-event-evt_998822"
    cb1 = process_payment_callback(
        db_session,
        tenant_context=env["ctx"],
        invoice_id=invoice.id,
        amount=150.0,
        provider="stripe",
        provider_reference="ch_123456789",
        idempotency_key=callback_idem_key,
    )
    assert cb1.method == "online"
    assert cb1.provider_reference == "stripe:ch_123456789"
    assert invoice.status == "paid"
    assert invoice.paid_amount == 150.0

    # Duplicate webhook callback
    cb2 = process_payment_callback(
        db_session,
        tenant_context=env["ctx"],
        invoice_id=invoice.id,
        amount=150.0,
        provider="stripe",
        provider_reference="ch_123456789",
        idempotency_key=callback_idem_key,
    )
    assert cb2.id == cb1.id
    assert invoice.paid_amount == 150.0


def test_payment_receipt_generation(db_session: Session):
    env = _setup_payment_env(db_session)

    invoice = create_invoice(
        db_session,
        tenant_context=env["ctx"],
        patient_id=env["patient"].id,
        branch_id=env["branch"].id,
        items=[
            {"description": "Urine Routine", "qty": 1.0, "unit_price": 80.0},
        ],
    )

    pmt = record_payment(
        db_session,
        tenant_context=env["ctx"],
        invoice_id=invoice.id,
        amount=30.0,
        method="card",
    )

    receipt = generate_receipt(db_session, tenant_context=env["ctx"], payment_id=pmt.id)
    assert receipt["receipt_no"] == pmt.receipt_no
    assert receipt["payment_amount"] == 30.0
    assert receipt["payment_method"] == "card"
    assert receipt["invoice_grand_total"] == 80.0
    assert receipt["invoice_paid_amount"] == 30.0
    assert receipt["invoice_balance_due"] == 50.0
    assert receipt["invoice_status"] == "part_paid"
    assert receipt["patient"]["full_name"] == "Bruce Wayne"


def test_rbac_authorization_for_payment(db_session: Session):
    env = _setup_payment_env(db_session)

    # Unauthorized user
    unauth_user = User(
        id=str(uuid.uuid4()),
        tenant_id=env["tenant"].id,
        username="unauth_user",
        email="unauth@example.com",
        hashed_password="fake-pw",
        full_name="Unauth User",
        is_active=True,
    )
    db_session.add(unauth_user)
    db_session.flush()

    unauth_ctx = TenantContext(
        tenant_id=env["tenant"].id,
        user_id=unauth_user.id,
        branch_id=env["branch"].id,
        is_superuser=False,
    )

    invoice = create_invoice(
        db_session,
        tenant_context=env["ctx"],
        patient_id=env["patient"].id,
        branch_id=env["branch"].id,
        items=[{"description": "Test Item", "qty": 1.0, "unit_price": 50.0}],
    )

    with pytest.raises(ForbiddenError, match="not authorized to collect payments"):
        record_payment(
            db_session,
            tenant_context=unauth_ctx,
            invoice_id=invoice.id,
            amount=50.0,
            method="cash",
        )


def test_tenant_isolation_on_payments(db_session: Session):
    env = _setup_payment_env(db_session)

    invoice = create_invoice(
        db_session,
        tenant_context=env["ctx"],
        patient_id=env["patient"].id,
        branch_id=env["branch"].id,
        items=[{"description": "Test Item", "qty": 1.0, "unit_price": 100.0}],
    )
    pmt = record_payment(
        db_session,
        tenant_context=env["ctx"],
        invoice_id=invoice.id,
        amount=50.0,
        method="cash",
    )

    other_tenant = Tenant(id=str(uuid.uuid4()), name="Other Clinic", code="OTHER")
    db_session.add(other_tenant)
    db_session.flush()

    other_ctx = TenantContext(tenant_id=other_tenant.id, user_id=str(uuid.uuid4()), is_superuser=False)

    with pytest.raises(NotFoundError):
        get_payment(db_session, tenant_context=other_ctx, payment_id=pmt.id)

    with pytest.raises(NotFoundError):
        generate_receipt(db_session, tenant_context=other_ctx, payment_id=pmt.id)

    with pytest.raises(NotFoundError):
        record_payment(
            db_session,
            tenant_context=other_ctx,
            invoice_id=invoice.id,
            amount=50.0,
            method="cash",
        )


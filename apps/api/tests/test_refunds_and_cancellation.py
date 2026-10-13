"""Tests for P04-05: Refunds and Cancellation (controlled refund flows, cancellations with reason, idempotency, RBAC, multi-tenant isolation, auditability)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.models.core import Tenant, Branch
from app.models.patient import Patient
from app.models.billing import Invoice, Payment, Refund
from app.models.identity import User, Role, UserRole, Permission, RolePermission
from app.security.tenant_guard import TenantContext
from app.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.billing.invoice_service import create_invoice, cancel_invoice, InvoiceStateTransitionError
from app.billing.payment_service import record_payment
from app.billing.refund_service import (
    process_refund,
    get_refund,
    list_refunds,
    generate_refund_no,
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


def _setup_refund_env(db_session: Session):
    tenant = Tenant(id=str(uuid.uuid4()), name="Metropolis Health", code="METRO", is_active=True)
    branch = Branch(id=str(uuid.uuid4()), tenant_id=tenant.id, name="Central Branch", code="CBR01")

    patient = Patient(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        patient_no="P-20001",
        first_name="Diana",
        last_name="Prince",
        sex="female",
        date_of_birth=datetime(1990, 5, 12).date(),
        mobile_normalized="+1555987654",
        created_at=datetime.now(timezone.utc),
    )

    user = User(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        username="billing_lead",
        email="lead@example.com",
        hashed_password="fake-hashed-pw",
        full_name="Billing Lead",
        is_active=True,
    )

    role = Role(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        name="Billing Lead Role",
        is_system=False,
    )
    p_refund = Permission(
        id=str(uuid.uuid4()),
        code="billing.refund",
        module="billing",
        resource="invoice",
        action="refund",
        risk_level="high",
    )
    p_cancel = Permission(
        id=str(uuid.uuid4()),
        code="billing.cancel",
        module="billing",
        resource="invoice",
        action="cancel",
        risk_level="high",
    )
    p_pay = Permission(
        id=str(uuid.uuid4()),
        code="billing.payment",
        module="billing",
        resource="payment",
        action="create",
        risk_level="normal",
    )
    rp_refund = RolePermission(role_id=role.id, permission_id=p_refund.id)
    rp_cancel = RolePermission(role_id=role.id, permission_id=p_cancel.id)
    rp_pay = RolePermission(role_id=role.id, permission_id=p_pay.id)
    user_role = UserRole(user_id=user.id, role_id=role.id)

    db_session.add_all([tenant, branch, patient, user, role, p_refund, p_cancel, p_pay, rp_refund, rp_cancel, rp_pay, user_role])
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
        "role": role,
        "ctx": ctx,
    }



def test_refund_full_and_partial_flow(db_session: Session):
    env = _setup_refund_env(db_session)
    ctx = env["ctx"]

    invoice = create_invoice(
        db_session,
        tenant_context=ctx,
        patient_id=env["patient"].id,
        branch_id=env["branch"].id,
        items=[
            {"description": "Thyroid Panel", "qty": 1.0, "unit_price": 100.0, "tax_rate_pct": 0.0},
        ],
    )
    assert invoice.grand_total == 100.0
    assert invoice.status == "issued"

    # Make full payment
    payment = record_payment(
        db_session,
        tenant_context=ctx,
        invoice_id=invoice.id,
        amount=100.0,
        method="upi",
    )
    assert invoice.status == "paid"
    assert invoice.paid_amount == 100.0
    assert invoice.refund_total == 0.0

    # Partial refund of 40
    ref1 = process_refund(
        db_session,
        tenant_context=ctx,
        invoice_id=invoice.id,
        amount=40.0,
        reason="Patient opted out of subtest T3",
        method="original_payment",
        payment_id=payment.id,
    )
    assert ref1.amount == 40.0
    assert ref1.refund_no.startswith("REF-")
    assert invoice.paid_amount == 60.0
    assert invoice.refund_total == 40.0
    assert invoice.status == "part_paid"

    # Exceeding remaining refundable balance (60) should fail
    with pytest.raises(ValidationError, match="exceeds available refundable balance"):
        process_refund(
            db_session,
            tenant_context=ctx,
            invoice_id=invoice.id,
            amount=70.0,
            reason="Excess refund",
        )

    # Remaining refund of 60
    ref2 = process_refund(
        db_session,
        tenant_context=ctx,
        invoice_id=invoice.id,
        amount=60.0,
        reason="Patient cancelled remaining tests",
        method="cash",
    )
    assert ref2.amount == 60.0
    assert invoice.paid_amount == 0.0
    assert invoice.refund_total == 100.0
    assert invoice.status == "refunded"

    # Further refund should be rejected as balance is 0
    with pytest.raises(ConflictError, match="no refundable balance"):
        process_refund(
            db_session,
            tenant_context=ctx,
            invoice_id=invoice.id,
            amount=10.0,
            reason="Extra refund",
        )


def test_refund_requires_reason_and_positive_amount(db_session: Session):
    env = _setup_refund_env(db_session)
    ctx = env["ctx"]

    invoice = create_invoice(
        db_session,
        tenant_context=ctx,
        patient_id=env["patient"].id,
        branch_id=env["branch"].id,
        items=[
            {"description": "ECG", "qty": 1.0, "unit_price": 50.0},
        ],
    )
    record_payment(
        db_session,
        tenant_context=ctx,
        invoice_id=invoice.id,
        amount=50.0,
        method="cash",
    )

    # Missing reason
    with pytest.raises(ValidationError, match="Refund reason is required"):
        process_refund(
            db_session,
            tenant_context=ctx,
            invoice_id=invoice.id,
            amount=20.0,
            reason="   ",
        )

    # Zero or negative amount
    with pytest.raises(ValidationError, match="Refund amount must be greater than 0"):
        process_refund(
            db_session,
            tenant_context=ctx,
            invoice_id=invoice.id,
            amount=0.0,
            reason="Zero refund",
        )




def test_refund_idempotency_and_numbering(db_session: Session):
    env = _setup_refund_env(db_session)
    ctx = env["ctx"]

    invoice = create_invoice(
        db_session,
        tenant_context=ctx,
        patient_id=env["patient"].id,
        branch_id=env["branch"].id,
        items=[
            {"description": "Lipid Profile", "qty": 1.0, "unit_price": 80.0},
        ],
    )
    record_payment(
        db_session,
        tenant_context=ctx,
        invoice_id=invoice.id,
        amount=80.0,
        method="card",
    )

    r_num = generate_refund_no(db_session, ctx.tenant_id)
    assert r_num.startswith("REF-")

    ref1 = process_refund(
        db_session,
        tenant_context=ctx,
        invoice_id=invoice.id,
        amount=30.0,
        reason="Duplicate charge reversal",
        idempotency_key="reversal-key-999",
    )
    ref2 = process_refund(
        db_session,
        tenant_context=ctx,
        invoice_id=invoice.id,
        amount=30.0,
        reason="Duplicate charge reversal",
        idempotency_key="reversal-key-999",
    )
    assert ref1.id == ref2.id
    assert invoice.refund_total == 30.0


def test_invoice_cancellation_flow_and_rbac(db_session: Session):
    env = _setup_refund_env(db_session)
    ctx = env["ctx"]

    invoice = create_invoice(
        db_session,
        tenant_context=ctx,
        patient_id=env["patient"].id,
        branch_id=env["branch"].id,
        items=[
            {"description": "Urine Routine", "qty": 1.0, "unit_price": 25.0},
        ],
    )

    # Missing cancellation reason
    with pytest.raises(ValidationError, match="Cancellation reason is required"):
        cancel_invoice(db_session, tenant_context=ctx, invoice_id=invoice.id, reason="")

    # Cancellation with unauthorized user
    unauth_user = User(
        id=str(uuid.uuid4()),
        tenant_id=env["tenant"].id,
        username="guest_user",
        email="guest@example.com",
        hashed_password="pw",
        full_name="Guest User",
        is_active=True,
    )
    db_session.add(unauth_user)
    db_session.flush()

    unauth_ctx = TenantContext(
        tenant_id=env["tenant"].id,
        user_id=unauth_user.id,
        branch_id=env["branch"].id,
    )

    with pytest.raises(ForbiddenError, match="User is not authorized to cancel invoices"):
        cancel_invoice(
            db_session,
            tenant_context=unauth_ctx,
            invoice_id=invoice.id,
            reason="Unauthorized attempt",
        )

    # Successful cancellation by authorized user
    cancelled = cancel_invoice(
        db_session,
        tenant_context=ctx,
        invoice_id=invoice.id,
        reason="Patient walked out before collection",
    )
    assert cancelled.status == "cancelled"
    assert cancelled.cancellation_reason == "Patient walked out before collection"

    # Cannot cancel already cancelled
    with pytest.raises(InvoiceStateTransitionError, match="Cannot cancel invoice in state 'cancelled'"):
        cancel_invoice(
            db_session,
            tenant_context=ctx,
            invoice_id=invoice.id,
            reason="Another cancel",
        )

    # Cannot refund cancelled invoice
    with pytest.raises(ConflictError, match="Cannot refund a cancelled invoice"):
        process_refund(
            db_session,
            tenant_context=ctx,
            invoice_id=invoice.id,
            amount=10.0,
            reason="Refund on cancelled",
        )



def test_refund_audit_logging_and_tenant_isolation(db_session: Session):
    env1 = _setup_refund_env(db_session)
    ctx1 = env1["ctx"]

    # Tenant 2
    t2 = Tenant(id=str(uuid.uuid4()), name="Gotham Health", code="GOTHAM", is_active=True)
    b2 = Branch(id=str(uuid.uuid4()), tenant_id=t2.id, name="Downtown Branch", code="DT01")
    ctx2 = TenantContext(tenant_id=t2.id, user_id=str(uuid.uuid4()), branch_id=b2.id)
    db_session.add_all([t2, b2])
    db_session.flush()

    inv = create_invoice(
        db_session,
        tenant_context=ctx1,
        patient_id=env1["patient"].id,
        branch_id=env1["branch"].id,
        items=[
            {"description": "Glucose Fasting", "qty": 1.0, "unit_price": 40.0},
        ],
    )
    record_payment(
        db_session,
        tenant_context=ctx1,
        invoice_id=inv.id,
        amount=40.0,
        method="cash",
    )

    # Process refund under tenant 1
    ref = process_refund(
        db_session,
        tenant_context=ctx1,
        invoice_id=inv.id,
        amount=40.0,
        reason="Patient fast broken prematurely",
        method="cash",
    )

    # Check audit log
    audits = get_audit_logs(db_session, tenant_id=ctx1.tenant_id, entity_type="refund", entity_id=ref.id)
    assert len(audits) >= 1
    assert audits[0].action_code == "invoice.refunded"
    assert audits[0].after_json["amount"] == 40.0
    assert audits[0].after_json["reason"] == "Patient fast broken prematurely"

    # Verify query
    fetched_ref = get_refund(db_session, tenant_context=ctx1, refund_id=ref.id)
    assert fetched_ref.id == ref.id

    # Cross-tenant access must fail with NotFoundError
    with pytest.raises(NotFoundError):
        get_refund(db_session, tenant_context=ctx2, refund_id=ref.id)

    # List refunds scoped to tenant 1
    t1_refunds, total1 = list_refunds(db_session, tenant_context=ctx1)
    assert total1 == 1
    assert len(t1_refunds) == 1

    t2_refunds, total2 = list_refunds(db_session, tenant_context=ctx2)
    assert total2 == 0
    assert len(t2_refunds) == 0


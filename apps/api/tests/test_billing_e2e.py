"""End-to-End Billing Lifecycle Test:
Patient -> Referral Partner & Rules -> Order -> Discount Engine -> Invoice -> Payment -> Commission Ledger -> Settlement.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.audit.service import get_audit_logs
from app.billing.commission_service import (
    accrue_commission_for_invoice,
    get_commission_ledger,
    list_commission_ledgers,
    settle_commission,
)
from app.billing.invoice_service import create_invoice, get_invoice, cancel_invoice
from app.billing.payment_service import record_payment, get_payment
from app.billing.pricing_service import create_price_list, add_item_to_price_list
from app.billing.referral_service import create_referral_partner, create_referral_rule
from app.billing.refund_service import process_refund
from app.db import Base
from app.models.billing import Invoice, Payment, CommissionLedger, ReferralPartner, ReferralRule, PriceList, PriceListItem
from app.models.core import Branch, Department, Tenant
from app.models.identity import Permission, Role, RolePermission, User, UserRole
from app.models.pathology import Test, Order, OrderItem
from app.models.patient import Patient
from app.pathology.order_workflow import create_order
from app.patient.service import register_patient
from app.security.tenant_guard import TenantContext


@pytest.fixture
def db_session_factory(tmp_path):
    db_file = tmp_path / "test_billing_e2e.db"
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


def _setup_billing_environment(session: Session):
    tenant = Tenant(name="Premier Diagnostics", code="PD-001", is_active=True)
    session.add(tenant)
    session.flush()

    branch = Branch(tenant_id=tenant.id, name="Central Lab", code="CEN-01", is_active=True)
    session.add(branch)
    session.flush()

    dept = Department(tenant_id=tenant.id, branch_id=branch.id, name="Clinical Pathology", code="CP", is_active=True)
    session.add(dept)
    session.flush()

    # Permissions
    perms = [
        Permission(code="patient.register", module="patient", resource="patient", action="register", risk_level="normal"),
        Permission(code="order.create", module="pathology", resource="order", action="create", risk_level="normal"),
        Permission(code="billing.create", module="billing", resource="invoice", action="create", risk_level="normal"),
        Permission(code="billing.payment", module="billing", resource="payment", action="create", risk_level="normal"),
        Permission(code="billing.refund", module="billing", resource="refund", action="create", risk_level="high"),
        Permission(code="billing.cancel", module="billing", resource="invoice", action="cancel", risk_level="high"),
        Permission(code="referral.view", module="referral", resource="partner", action="view", risk_level="normal"),
        Permission(code="referral.rule.manage", module="referral", resource="rule", action="manage", risk_level="high"),
        Permission(code="referral.commission.view", module="referral", resource="commission", action="view", risk_level="normal"),
        Permission(code="referral.commission.settle", module="referral", resource="commission", action="settle", risk_level="high"),
        Permission(code="pricing.view", module="billing", resource="price_list", action="view", risk_level="normal"),
        Permission(code="pricing.manage", module="billing", resource="price_list", action="manage", risk_level="high"),
    ]
    session.add_all(perms)
    session.flush()

    role_admin = Role(tenant_id=tenant.id, name="Billing Administrator", is_system=False)
    session.add(role_admin)
    session.flush()

    for p in perms:
        session.add(RolePermission(role_id=role_admin.id, permission_id=p.id, allow=True))

    user_admin = User(tenant_id=tenant.id, email="admin@premier.com", username="admin_bill", hashed_password="pw")
    session.add(user_admin)
    session.flush()
    session.add(UserRole(user_id=user_admin.id, role_id=role_admin.id))

    # Catalog tests
    test_cbc = Test(
        tenant_id=tenant.id,
        code="CBC",
        name="Complete Blood Count",
        display_name="CBC",
        department_id=dept.id,
    )
    test_lipid = Test(
        tenant_id=tenant.id,
        code="LIPID",
        name="Lipid Profile",
        display_name="Lipid",
        department_id=dept.id,
    )
    session.add_all([test_cbc, test_lipid])
    session.flush()

    # Price list
    ctx = TenantContext(tenant_id=tenant.id, branch_id=branch.id, user_id=user_admin.id)
    price_list = create_price_list(
        session,
        tenant_context=ctx,
        name="Standard OPD Rates",
        code="OPD-STD",
        is_default=True,
    )
    add_item_to_price_list(
        session,
        tenant_context=ctx,
        price_list_id=price_list.id,
        item_type="test",
        item_id=test_cbc.id,
        rate=50.00,
        max_discount_pct=25.0,
    )
    add_item_to_price_list(
        session,
        tenant_context=ctx,
        price_list_id=price_list.id,
        item_type="test",
        item_id=test_lipid.id,
        rate=120.00,
        max_discount_pct=25.0,
    )

    session.commit()

    return {
        "tenant": tenant,
        "branch": branch,
        "dept": dept,
        "user_admin": user_admin,
        "ctx": ctx,
        "test_cbc": test_cbc,
        "test_lipid": test_lipid,
        "price_list": price_list,
    }


def test_full_patient_to_commission_e2e_flow(db_session_factory):
    session = db_session_factory()
    env = _setup_billing_environment(session)
    ctx = env["ctx"]

    # 1. Patient Registration
    patient = register_patient(
        session,
        tenant_context=ctx,
        first_name="Robert",
        last_name="Langdon",
        mobile="+15551234567",
        sex="male",
    )
    assert patient.id is not None
    assert patient.first_name == "Robert"

    # 2. Referral Partner and Rules setup
    partner = create_referral_partner(
        session,
        tenant_context=ctx,
        partner_type="doctor",
        name="Dr. Arthur Conan",
        phone="+15559876543",
    )
    # Global rule: 10% patient discount, 15% commission
    create_referral_rule(
        session,
        tenant_context=ctx,
        partner_id=partner.id,
        scope_type="all",
        patient_discount_pct=10.0,
        commission_pct=15.0,
        priority=100,
    )
    # Specific rule for Lipid: 20% patient discount, 25% commission + 10.0 fixed
    create_referral_rule(
        session,
        tenant_context=ctx,
        partner_id=partner.id,
        scope_type="test",
        scope_id=env["test_lipid"].id,
        patient_discount_pct=20.0,
        commission_pct=25.0,
        commission_fixed=10.0,
        priority=10,
    )

    # 3. Pathology Order Creation linked to patient and referrer
    order = create_order(
        session,
        tenant_context=ctx,
        patient_id=patient.id,
        referral_partner_id=partner.id,
        test_ids=[env["test_cbc"].id, env["test_lipid"].id],
        branch_id=env["branch"].id,
    )
    assert order.id is not None
    assert len(order.items) == 2

    # 4. Invoice generation from order
    # CBC: base 50.00, referral discount 10% = 5.00 -> net 45.00
    # Lipid: base 120.00, referral discount 20% = 24.00 -> net 96.00
    # Grand total: 45.00 + 96.00 = 141.00
    invoice = create_invoice(
        session,
        tenant_context=ctx,
        patient_id=patient.id,
        order_id=order.id,
    )
    assert invoice.id is not None
    assert invoice.status == "issued"
    assert invoice.referral_partner_id == partner.id
    assert float(invoice.subtotal) == 170.00
    assert float(invoice.discount_total) == 29.00
    assert float(invoice.grand_total) == 141.00
    assert float(invoice.paid_amount) == 0.00

    # 5. Commission Accrual against the invoice
    # CBC line: 45.00 * 15% = 6.75
    # Lipid line: (96.00 * 25%) + 10.00 = 24.00 + 10.00 = 34.00
    # Total Commission: 6.75 + 34.00 = 40.75
    comm_ledger = accrue_commission_for_invoice(
        session,
        tenant_context=ctx,
        invoice_id=invoice.id,
    )
    assert comm_ledger is not None
    assert comm_ledger.status == "pending"
    assert float(comm_ledger.amount) == 40.75

    # 6. Payment Collection against Invoice
    # Split payment: $100 cash + $41 card
    pay1 = record_payment(
        session,
        tenant_context=ctx,
        invoice_id=invoice.id,
        amount=100.00,
        method="cash",
        idempotency_key="PAY-E2E-001",
    )
    assert pay1.status == "success"
    session.refresh(invoice)
    assert invoice.status == "part_paid"
    assert float(invoice.paid_amount) == 100.00

    pay2 = record_payment(
        session,
        tenant_context=ctx,
        invoice_id=invoice.id,
        amount=41.00,
        method="card",
        idempotency_key="PAY-E2E-002",
        provider_reference="CARD-TXN-9988",
    )
    assert pay2.status == "success"
    session.refresh(invoice)
    assert invoice.status == "paid"
    assert float(invoice.paid_amount) == 141.00

    # 7. Settle Commission
    settled = settle_commission(
        session,
        tenant_context=ctx,
        ledger_ids=[comm_ledger.id],
        settlement_reference="E2E-SETTLE-BATCH-1",
        notes="Monthly doctor commission payout",
    )
    assert len(settled) == 1
    assert settled[0].status == "settled"
    assert settled[0].settlement_reference == "E2E-SETTLE-BATCH-1"
    assert settled[0].settled_at is not None

    # 8. Verify audit logs recorded across the whole chain
    patient_audits = get_audit_logs(session, tenant_id=ctx.tenant_id, entity_type="patient")
    assert len(patient_audits) >= 1

    inv_audits = get_audit_logs(session, tenant_id=ctx.tenant_id, entity_type="invoice")
    assert any(a.action_code == "invoice.created" for a in inv_audits)

    pay_audits = get_audit_logs(session, tenant_id=ctx.tenant_id, entity_type="payment")
    assert len(pay_audits) == 2

    comm_audits = get_audit_logs(session, tenant_id=ctx.tenant_id, entity_type="commission_ledger")
    assert any(a.action_code == "referral.commission.calculated" for a in comm_audits)
    assert any(a.action_code == "referral.commission.settled" for a in comm_audits)



def test_cancellation_refund_and_commission_reversal_e2e_flow(db_session_factory):
    session = db_session_factory()
    env = _setup_billing_environment(session)
    ctx = env["ctx"]

    # Register patient
    patient = register_patient(
        session,
        tenant_context=ctx,
        first_name="Alice",
        last_name="Wonderland",
        mobile="+15557778888",
        sex="female",
    )

    # Referral partner with 10% commission
    partner = create_referral_partner(
        session,
        tenant_context=ctx,
        partner_type="doctor",
        name="Dr. John Watson",
    )
    create_referral_rule(
        session,
        tenant_context=ctx,
        partner_id=partner.id,
        scope_type="all",
        commission_pct=10.0,
    )

    # Create Invoice directly
    invoice = create_invoice(
        session,
        tenant_context=ctx,
        patient_id=patient.id,
        referral_partner_id=partner.id,
        items=[
            {"item_type": "test", "item_id": env["test_cbc"].id, "description": "CBC", "unit_price": 50.0, "qty": 1},
        ],
    )
    assert invoice.grand_total == 50.0

    # Accrue commission
    ledger = accrue_commission_for_invoice(session, tenant_context=ctx, invoice_id=invoice.id)
    assert ledger.status == "pending"
    assert float(ledger.amount) == 5.00

    # Scenario A: Cancel invoice prior to payment
    cancel_invoice(
        session,
        tenant_context=ctx,
        invoice_id=invoice.id,
        reason="Patient withdrew consent prior to blood draw",
    )
    session.refresh(invoice)
    session.refresh(ledger)
    assert invoice.status == "cancelled"
    assert ledger.status == "cancelled"

    # Scenario B: Second invoice with payment and subsequent refund
    invoice2 = create_invoice(
        session,
        tenant_context=ctx,
        patient_id=patient.id,
        referral_partner_id=partner.id,
        items=[
            {"item_type": "test", "item_id": env["test_lipid"].id, "description": "Lipid", "unit_price": 120.0, "qty": 1},
        ],
    )
    pay = record_payment(
        session,
        tenant_context=ctx,
        invoice_id=invoice2.id,
        amount=120.0,
        method="upi",
        idempotency_key="PAY-UPI-REFUND-01",
    )
    session.refresh(invoice2)
    assert invoice2.status == "paid"

    # Process refund
    ref = process_refund(
        session,
        tenant_context=ctx,
        invoice_id=invoice2.id,
        payment_id=pay.id,
        amount=120.0,
        reason="Analyzer breakdown / test cancelled by lab",
        method="original_payment",
        idempotency_key="REFUND-UPI-01",
    )
    session.refresh(invoice2)
    assert invoice2.status == "refunded"
    assert float(invoice2.refund_total) == 120.0


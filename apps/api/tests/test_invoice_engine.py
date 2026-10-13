"""Tests for P04-02: Invoice Engine (creation, line-level calculation, pricing lookup, state machine, and line-level auditability)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.models.core import Tenant, Branch
from app.models.pathology import Test, Order, OrderItem
from app.models.patient import Patient
from app.models.billing import PriceList, PriceListItem, Invoice, InvoiceItem
from app.security.tenant_guard import TenantContext
from app.errors import NotFoundError, ValidationError
from app.billing.pricing_service import create_price_list, add_item_to_price_list
from app.billing.invoice_service import (
    create_invoice,
    get_invoice,
    list_invoices,
    cancel_invoice,
    InvoiceNotFoundError,
    InvoiceStateTransitionError,
    generate_invoice_no,
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


@pytest.fixture
def invoice_test_setup(db_session: Session):
    tenant = Tenant(id=str(uuid.uuid4()), name="Metropolis Health", code="METRO", is_active=True)
    branch = Branch(id=str(uuid.uuid4()), tenant_id=tenant.id, name="Central Branch", code="CBR01")

    patient = Patient(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        first_name="Jane",
        last_name="Doe",
        patient_no="P-100001",
        sex="female",
    )

    t_fbc = Test(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        code="FBC",
        name="Full Blood Count",
        display_name="Full Blood Count",
    )
    t_esr = Test(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        code="ESR",
        name="Erythrocyte Sedimentation Rate",
        display_name="ESR",
    )

    db_session.add_all([tenant, branch, patient, t_fbc, t_esr])
    db_session.commit()

    # Create a tenant default price list with prices for FBC and ESR
    default_pl = create_price_list(
        db_session,
        tenant_context=TenantContext(tenant_id=tenant.id, branch_id=branch.id),
        code="STANDARD",
        name="Standard Price List",
        is_default=True,
    )
    add_item_to_price_list(
        db_session,
        tenant_context=TenantContext(tenant_id=tenant.id, branch_id=branch.id),
        price_list_id=default_pl.id,
        item_type="test",
        item_id=t_fbc.id,
        rate=35.0,
    )
    add_item_to_price_list(
        db_session,
        tenant_context=TenantContext(tenant_id=tenant.id, branch_id=branch.id),
        price_list_id=default_pl.id,
        item_type="test",
        item_id=t_esr.id,
        rate=15.0,
    )

    ctx = TenantContext(tenant_id=tenant.id, branch_id=branch.id, user_id=str(uuid.uuid4()))
    return {
        "tenant": tenant,
        "branch": branch,
        "patient": patient,
        "fbc": t_fbc,
        "esr": t_esr,
        "ctx": ctx,
    }


def test_create_invoice_with_explicit_line_items(db_session: Session, invoice_test_setup: dict):
    env = invoice_test_setup
    ctx = env["ctx"]

    items_data = [
        {
            "description": "Full Blood Count",
            "qty": 1.0,
            "unit_price": 40.0,
            "discount_pct": 10.0,  # 4.0 discount -> 36.0
            "tax_rate_pct": 5.0,   # 5% of 36.0 = 1.80 -> 37.80
        },
        {
            "description": "ESR",
            "qty": 2.0,
            "unit_price": 20.0,    # gross 40.0
            "discount_amount": 5.0, # net 35.0
            "tax_rate_pct": 0.0,
        },
    ]

    inv = create_invoice(
        db_session,
        tenant_context=ctx,
        patient_id=env["patient"].id,
        items=items_data,
        currency="USD",
        notes="First consultation invoice",
    )

    assert inv.id is not None
    assert inv.invoice_no.startswith("INV-")
    assert inv.status == "issued"
    assert len(inv.items) == 2

    # Line 1: gross 40.0, discount 4.0, net 36.0, tax 1.80, total 37.80
    # Line 2: gross 40.0, discount 5.0, net 35.0, tax 0.0, total 35.00
    # Totals: Subtotal 80.0, Discount 9.0, Tax 1.80, Grand Total 72.80
    assert float(inv.subtotal) == 80.0
    assert float(inv.discount_total) == 9.0
    assert float(inv.tax_total) == 1.80
    assert float(inv.grand_total) == 72.80

    item1 = inv.items[0]
    assert float(item1.discount_amount) == 4.0
    assert float(item1.tax_amount) == 1.80
    assert float(item1.line_total) == 37.80

    # Line-level audit trail verification
    audits = get_audit_logs(db_session, tenant_id=ctx.tenant_id, entity_type="invoice", entity_id=inv.id)
    assert len(audits) >= 1
    create_audit = next(a for a in audits if a.action_code == "invoice.created")
    assert create_audit.after_json["grand_total"] == 72.80
    assert len(create_audit.after_json["line_items"]) == 2
    assert create_audit.after_json["line_items"][0]["description"] == "Full Blood Count"


def test_create_invoice_resolving_price_list_rates(db_session: Session, invoice_test_setup: dict):
    env = invoice_test_setup
    ctx = env["ctx"]

    pl = create_price_list(
        db_session,
        tenant_context=ctx,
        code="BRANCH_SPECIAL",
        name="Branch Special Price List",
        branch_id=env["branch"].id,
        is_default=True,
    )
    add_item_to_price_list(
        db_session,
        tenant_context=ctx,
        price_list_id=pl.id,
        item_type="test",
        item_id=env["fbc"].id,
        rate=55.0,
    )

    items_data = [
        {
            "item_type": "test",
            "item_id": env["fbc"].id,
            "qty": 1.0,
        },
        {
            "item_type": "test",
            "item_id": env["esr"].id,
            "qty": 1.0,
        },
    ]

    inv = create_invoice(
        db_session,
        tenant_context=ctx,
        patient_id=env["patient"].id,
        items=items_data,
    )

    assert inv.subtotal == 70.0  # 55.0 + 15.0
    assert inv.grand_total == 70.0
    fbc_item = next(it for it in inv.items if it.item_id == env["fbc"].id)
    assert fbc_item.unit_price == 55.0
    esr_item = next(it for it in inv.items if it.item_id == env["esr"].id)
    assert esr_item.unit_price == 15.0



def test_create_invoice_from_pathology_order(db_session: Session, invoice_test_setup: dict):
    env = invoice_test_setup
    ctx = env["ctx"]

    order = Order(
        id=str(uuid.uuid4()),
        tenant_id=ctx.tenant_id,
        branch_id=env["branch"].id,
        patient_id=env["patient"].id,
        order_no="ORD-20261013-0001",
        status="placed",
    )
    oi1 = OrderItem(
        id=str(uuid.uuid4()),
        order_id=order.id,
        test_id=env["fbc"].id,
        status="placed",
    )
    oi2 = OrderItem(
        id=str(uuid.uuid4()),
        order_id=order.id,
        test_id=env["esr"].id,
        status="placed",
    )
    order.items = [oi1, oi2]
    db_session.add(order)
    db_session.commit()

    inv = create_invoice(
        db_session,
        tenant_context=ctx,
        patient_id=env["patient"].id,
        order_id=order.id,
    )

    assert inv.order_id == order.id
    assert len(inv.items) == 2
    assert inv.subtotal == 50.0  # 35.0 (fbc) + 15.0 (esr)
    assert inv.grand_total == 50.0
    assert {it.order_item_id for it in inv.items} == {oi1.id, oi2.id}


def test_invoice_state_machine_and_cancellation(db_session: Session, invoice_test_setup: dict):
    env = invoice_test_setup
    ctx = env["ctx"]

    inv = create_invoice(
        db_session,
        tenant_context=ctx,
        patient_id=env["patient"].id,
        items=[{"description": "Consultation", "qty": 1, "unit_price": 50}],
    )

    assert inv.status == "issued"

    with pytest.raises(ValidationError, match="Cancellation reason is required"):
        cancel_invoice(db_session, tenant_context=ctx, invoice_id=inv.id, reason="")

    cancelled_inv = cancel_invoice(
        db_session,
        tenant_context=ctx,
        invoice_id=inv.id,
        reason="Patient requested refund before tests performed",
    )
    assert cancelled_inv.status == "cancelled"
    assert cancelled_inv.cancellation_reason == "Patient requested refund before tests performed"

    with pytest.raises(InvoiceStateTransitionError, match="Cannot cancel invoice in state 'cancelled'"):
        cancel_invoice(db_session, tenant_context=ctx, invoice_id=inv.id, reason="Duplicate cancel")

    audits = get_audit_logs(db_session, tenant_id=ctx.tenant_id, entity_type="invoice", entity_id=inv.id)
    cancel_audit = next(a for a in audits if a.action_code == "invoice.cancelled")
    assert cancel_audit.before_json["status"] == "issued"
    assert cancel_audit.after_json["status"] == "cancelled"


def test_tenant_isolation_invoices(db_session: Session, invoice_test_setup: dict):
    env = invoice_test_setup
    ctx = env["ctx"]

    other_tenant = Tenant(id=str(uuid.uuid4()), name="Other Hospital", code="OTH", is_active=True)
    other_ctx = TenantContext(tenant_id=other_tenant.id, user_id=str(uuid.uuid4()))
    db_session.add(other_tenant)
    db_session.commit()

    inv = create_invoice(
        db_session,
        tenant_context=ctx,
        patient_id=env["patient"].id,
        items=[{"description": "Fee", "qty": 1, "unit_price": 100}],
    )

    with pytest.raises(InvoiceNotFoundError):
        get_invoice(db_session, tenant_context=other_ctx, invoice_id=inv.id)

    with pytest.raises(InvoiceNotFoundError):
        cancel_invoice(db_session, tenant_context=other_ctx, invoice_id=inv.id, reason="Unauthorized")

    invoices, count = list_invoices(db_session, tenant_context=other_ctx)
    assert count == 0
    assert len(invoices) == 0

    invoices, count = list_invoices(db_session, tenant_context=ctx)
    assert count == 1
    assert invoices[0].id == inv.id


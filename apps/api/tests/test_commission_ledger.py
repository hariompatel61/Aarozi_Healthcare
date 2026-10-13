"""Tests for P04-07: Referral Commission Ledger (Rule resolution, accrual, settlement, RBAC, multi-tenancy, audit)."""
import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.audit.service import get_audit_logs
from app.billing.commission_service import (
    CommissionLedgerNotFoundError,
    accrue_commission_for_invoice,
    accrue_manual_commission,
    cancel_commission_for_invoice,
    get_commission_ledger,
    list_commission_ledgers,
    resolve_commission_rule,
    settle_commission,
)
from app.billing.invoice_service import cancel_invoice, create_invoice
from app.billing.referral_service import create_referral_partner, create_referral_rule
from app.db import Base
from app.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.billing import CommissionLedger, Invoice, ReferralPartner, ReferralRule
from app.models.core import Branch, Department, Tenant
from app.models.identity import Permission, Role, RolePermission, User, UserRole
from app.models.pathology import Test
from app.models.patient import Patient
from app.security.tenant_guard import TenantContext


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


def _setup_commission_env(db: Session):
    tenant1 = Tenant(name="Alpha Hospital", code="ALPHA-01")
    tenant2 = Tenant(name="Beta Diagnostics", code="BETA-02")
    db.add_all([tenant1, tenant2])
    db.flush()

    branch1 = Branch(tenant_id=tenant1.id, name="Main Branch", code="MB-01")
    branch2 = Branch(tenant_id=tenant2.id, name="Branch Beta", code="BB-01")
    db.add_all([branch1, branch2])
    db.flush()

    dept_biochem = Department(tenant_id=tenant1.id, branch_id=branch1.id, name="Biochemistry", code="BIO")
    dept_hemato = Department(tenant_id=tenant1.id, branch_id=branch1.id, name="Hematology", code="HEM")
    db.add_all([dept_biochem, dept_hemato])
    db.flush()

    test_cbc = Test(
        tenant_id=tenant1.id,
        code="CBC",
        name="Complete Blood Count",
        display_name="CBC",
        department_id=dept_hemato.id,
    )
    test_lft = Test(
        tenant_id=tenant1.id,
        code="LFT",
        name="Liver Function Test",
        display_name="LFT",
        department_id=dept_biochem.id,
    )
    db.add_all([test_cbc, test_lft])

    patient1 = Patient(tenant_id=tenant1.id, patient_no="PAT-001", first_name="John", last_name="Doe", sex="male")
    patient2 = Patient(tenant_id=tenant2.id, patient_no="PAT-002", first_name="Jane", last_name="Smith", sex="female")
    db.add_all([patient1, patient2])

    perm_comm_view = Permission(
        code="referral.commission.view",
        module="referral",
        resource="commission",
        action="view",
        risk_level="normal",
    )
    perm_comm_settle = Permission(
        code="referral.commission.settle",
        module="referral",
        resource="commission",
        action="settle",
        risk_level="high",
    )
    perm_inv_cancel = Permission(
        code="billing.cancel",
        module="billing",
        resource="invoice",
        action="cancel",
        risk_level="high",
    )
    perm_ref_manage = Permission(
        code="referral.rule.manage",
        module="referral",
        resource="rule",
        action="manage",
        risk_level="high",
    )
    db.add_all([perm_comm_view, perm_comm_settle, perm_inv_cancel, perm_ref_manage])
    db.flush()

    role_settler = Role(tenant_id=tenant1.id, name="Accountant", is_system=False)
    role_viewer = Role(tenant_id=tenant1.id, name="Audit Viewer", is_system=False)
    db.add_all([role_settler, role_viewer])
    db.flush()

    db.add_all([
        RolePermission(role_id=role_settler.id, permission_id=perm_comm_view.id, allow=True),
        RolePermission(role_id=role_settler.id, permission_id=perm_comm_settle.id, allow=True),
        RolePermission(role_id=role_settler.id, permission_id=perm_inv_cancel.id, allow=True),
        RolePermission(role_id=role_settler.id, permission_id=perm_ref_manage.id, allow=True),
        RolePermission(role_id=role_viewer.id, permission_id=perm_comm_view.id, allow=True),
    ])

    user_settler = User(tenant_id=tenant1.id, email="settler@alpha.com", username="settler", hashed_password="pw")
    user_viewer = User(tenant_id=tenant1.id, email="viewer@alpha.com", username="viewer", hashed_password="pw")
    user_unauth = User(tenant_id=tenant1.id, email="unauth@alpha.com", username="unauth", hashed_password="pw")
    db.add_all([user_settler, user_viewer, user_unauth])
    db.flush()

    db.add_all([
        UserRole(user_id=user_settler.id, role_id=role_settler.id),
        UserRole(user_id=user_viewer.id, role_id=role_viewer.id),
    ])
    db.commit()

    return {
        "tenant1": tenant1,
        "tenant2": tenant2,
        "branch1": branch1,
        "branch2": branch2,
        "dept_biochem": dept_biochem,
        "dept_hemato": dept_hemato,
        "test_cbc": test_cbc,
        "test_lft": test_lft,
        "patient1": patient1,
        "patient2": patient2,
        "user_settler": user_settler,
        "user_viewer": user_viewer,
        "user_unauth": user_unauth,
        "ctx1_settler": TenantContext(tenant_id=tenant1.id, branch_id=branch1.id, user_id=user_settler.id),
        "ctx1_viewer": TenantContext(tenant_id=tenant1.id, branch_id=branch1.id, user_id=user_viewer.id),
        "ctx1_unauth": TenantContext(tenant_id=tenant1.id, branch_id=branch1.id, user_id=user_unauth.id),
        "ctx2": TenantContext(tenant_id=tenant2.id, branch_id=branch2.id, user_id=str(uuid.uuid4())),
    }


def test_rule_resolution_and_commission_accrual(db_session: Session):
    env = _setup_commission_env(db_session)
    ctx = env["ctx1_settler"]

    partner = create_referral_partner(
        db_session,
        tenant_context=ctx,
        partner_type="doctor",
        name="Dr. Gregory House",
    )

    # 1. Global rule: 10% commission
    create_referral_rule(
        db_session,
        tenant_context=ctx,
        partner_id=partner.id,
        scope_type="all",
        commission_pct=10.0,
        priority=100,
    )

    # 2. Dept rule for Biochemistry: 15% commission + 5.0 fixed
    create_referral_rule(
        db_session,
        tenant_context=ctx,
        partner_id=partner.id,
        scope_type="department",
        scope_id=env["dept_biochem"].id,
        commission_pct=15.0,
        commission_fixed=5.0,
        priority=50,
    )

    # 3. Specific rule for CBC: 20% commission (no fixed)
    create_referral_rule(
        db_session,
        tenant_context=ctx,
        partner_id=partner.id,
        scope_type="test",
        scope_id=env["test_cbc"].id,
        commission_pct=20.0,
        priority=10,
    )

    # Invoice with 3 items:
    # Item 1: CBC ($50.00) -> CBC rule (20% of 50 = 10.00)
    # Item 2: LFT ($100.00, in Biochem) -> Biochem rule (15% of 100 = 15.00 + 5.00 = 20.00)
    # Item 3: Fee ($30.00, type 'fee') -> Global rule (10% of 30 = 3.00)
    invoice = create_invoice(
        db_session,
        tenant_context=ctx,
        patient_id=env["patient1"].id,
        referral_partner_id=partner.id,
        items=[
            {"item_type": "test", "item_id": env["test_cbc"].id, "description": "CBC", "unit_price": 50.0, "qty": 1},
            {"item_type": "test", "item_id": env["test_lft"].id, "description": "LFT", "unit_price": 100.0, "qty": 1},
            {"item_type": "fee", "item_id": None, "description": "Collection Fee", "unit_price": 30.0, "qty": 1},
        ],
    )

    ledger = accrue_commission_for_invoice(
        db_session,
        tenant_context=ctx,
        invoice_id=invoice.id,
    )

    assert ledger is not None
    assert ledger.referral_partner_id == partner.id
    assert ledger.invoice_id == invoice.id
    assert ledger.status == "pending"
    # Total expected: 10.00 + 20.00 + 3.00 = 33.00
    assert float(ledger.amount) == 33.00

    breakdown = json.loads(ledger.breakdown_json)
    assert len(breakdown) == 3
    assert breakdown[0]["commission_amount"] == 10.0
    assert breakdown[1]["commission_amount"] == 20.0
    assert breakdown[2]["commission_amount"] == 3.0

    audit_logs = get_audit_logs(
        db_session,
        tenant_id=ctx.tenant_id,
        entity_type="commission_ledger",
        entity_id=ledger.id,
    )
    assert any(log.action_code == "referral.commission.calculated" for log in audit_logs)


def test_commission_settlement_lifecycle(db_session: Session):
    env = _setup_commission_env(db_session)
    ctx_settler = env["ctx1_settler"]
    ctx_viewer = env["ctx1_viewer"]
    ctx_unauth = env["ctx1_unauth"]

    partner = create_referral_partner(
        db_session,
        tenant_context=ctx_settler,
        partner_type="doctor",
        name="Dr. James Wilson",
    )
    create_referral_rule(
        db_session,
        tenant_context=ctx_settler,
        partner_id=partner.id,
        scope_type="all",
        commission_pct=10.0,
    )

    inv = create_invoice(
        db_session,
        tenant_context=ctx_settler,
        patient_id=env["patient1"].id,
        referral_partner_id=partner.id,
        items=[{"item_type": "test", "description": "General", "unit_price": 200.0, "qty": 1}],
    )

    ledger = accrue_commission_for_invoice(db_session, tenant_context=ctx_settler, invoice_id=inv.id)
    assert ledger.status == "pending"
    assert float(ledger.amount) == 20.00

    # Viewer or unauthenticated user cannot settle
    with pytest.raises(ForbiddenError):
        settle_commission(
            db_session,
            tenant_context=ctx_viewer,
            ledger_ids=[ledger.id],
        )

    with pytest.raises(ForbiddenError):
        settle_commission(
            db_session,
            tenant_context=ctx_unauth,
            ledger_ids=[ledger.id],
        )

    # Settler user settles successfully
    settled_list = settle_commission(
        db_session,
        tenant_context=ctx_settler,
        ledger_ids=[ledger.id],
        settlement_reference="CHQ-2026-9901",
        notes="Settled via monthly batch",
    )
    assert len(settled_list) == 1
    assert settled_list[0].status == "settled"
    assert settled_list[0].settlement_reference == "CHQ-2026-9901"
    assert settled_list[0].settled_at is not None
    assert settled_list[0].settled_by == ctx_settler.user_id

    # Settling again raises NotFoundError
    with pytest.raises(NotFoundError):
        settle_commission(
            db_session,
            tenant_context=ctx_settler,
            ledger_ids=[ledger.id],
        )

    # Re-accruing settled invoice raises ConflictError
    with pytest.raises(ConflictError):
        accrue_commission_for_invoice(
            db_session,
            tenant_context=ctx_settler,
            invoice_id=inv.id,
        )



def test_manual_commission_accrual(db_session: Session):
    env = _setup_commission_env(db_session)
    ctx = env["ctx1_settler"]

    partner = create_referral_partner(
        db_session,
        tenant_context=ctx,
        partner_type="hospital",
        name="Mercy Hospital",
    )

    manual_ledger = accrue_manual_commission(
        db_session,
        tenant_context=ctx,
        referral_partner_id=partner.id,
        amount=150.50,
        notes="Quarterly bonus entitlement",
    )

    assert manual_ledger.id is not None
    assert float(manual_ledger.amount) == 150.50
    assert manual_ledger.status == "pending"
    assert manual_ledger.notes == "Quarterly bonus entitlement"

    # Negative amount raises validation error
    with pytest.raises(ValidationError):
        accrue_manual_commission(
            db_session,
            tenant_context=ctx,
            referral_partner_id=partner.id,
            amount=-20.00,
        )


def test_invoice_cancellation_cancels_pending_commission(db_session: Session):
    env = _setup_commission_env(db_session)
    ctx = env["ctx1_settler"]

    partner = create_referral_partner(
        db_session,
        tenant_context=ctx,
        partner_type="doctor",
        name="Dr. Allison Cameron",
    )
    create_referral_rule(
        db_session,
        tenant_context=ctx,
        partner_id=partner.id,
        scope_type="all",
        commission_pct=12.0,
    )

    inv = create_invoice(
        db_session,
        tenant_context=ctx,
        patient_id=env["patient1"].id,
        referral_partner_id=partner.id,
        items=[{"item_type": "test", "description": "Glucose", "unit_price": 100.0, "qty": 1}],
    )

    ledger = accrue_commission_for_invoice(db_session, tenant_context=ctx, invoice_id=inv.id)
    assert ledger.status == "pending"

    # Cancel invoice
    cancel_invoice(
        db_session,
        tenant_context=ctx,
        invoice_id=inv.id,
        reason="Patient requested test cancellation",
    )

    refreshed_ledger = get_commission_ledger(db_session, tenant_context=ctx, ledger_id=ledger.id)
    assert refreshed_ledger.status == "cancelled"

    # Accruing for a cancelled invoice is rejected
    with pytest.raises(ConflictError):
        accrue_commission_for_invoice(db_session, tenant_context=ctx, invoice_id=inv.id)


def test_rbac_and_tenant_isolation(db_session: Session):
    env = _setup_commission_env(db_session)
    ctx1 = env["ctx1_settler"]
    ctx1_viewer = env["ctx1_viewer"]
    ctx1_unauth = env["ctx1_unauth"]
    ctx2 = env["ctx2"]

    partner1 = create_referral_partner(
        db_session,
        tenant_context=ctx1,
        partner_type="doctor",
        name="Dr. Eric Foreman",
    )
    create_referral_rule(
        db_session,
        tenant_context=ctx1,
        partner_id=partner1.id,
        scope_type="all",
        commission_pct=10.0,
    )

    inv1 = create_invoice(
        db_session,
        tenant_context=ctx1,
        patient_id=env["patient1"].id,
        referral_partner_id=partner1.id,
        items=[{"item_type": "test", "description": "Basic Checkup", "unit_price": 100.0, "qty": 1}],
    )

    ledger1 = accrue_commission_for_invoice(db_session, tenant_context=ctx1, invoice_id=inv1.id)

    # 1. RBAC view permissions: Viewer can view
    view_entry = get_commission_ledger(db_session, tenant_context=ctx1_viewer, ledger_id=ledger1.id)
    assert view_entry.id == ledger1.id

    items, count = list_commission_ledgers(db_session, tenant_context=ctx1_viewer)
    assert count == 1
    assert len(items) == 1

    # Unauthorized user cannot view
    with pytest.raises(ForbiddenError):
        get_commission_ledger(db_session, tenant_context=ctx1_unauth, ledger_id=ledger1.id)

    with pytest.raises(ForbiddenError):
        list_commission_ledgers(db_session, tenant_context=ctx1_unauth)

    # 2. Multi-tenant isolation: Tenant 2 cannot see Tenant 1 ledger
    with pytest.raises(CommissionLedgerNotFoundError):
        get_commission_ledger(db_session, tenant_context=ctx2, ledger_id=ledger1.id)

    items2, count2 = list_commission_ledgers(db_session, tenant_context=ctx2)
    assert count2 == 0
    assert len(items2) == 0

    # 3. Bounded pagination check: list supports bounded pagination
    items_paged, _ = list_commission_ledgers(db_session, tenant_context=ctx1_viewer, limit=1000)
    assert len(items_paged) <= 100


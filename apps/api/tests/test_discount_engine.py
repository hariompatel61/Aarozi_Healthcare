"""Tests for P04-03 Discount Engine.

Verifies:
1. Referral discount resolution based on scope and priority (item direct match > department > all).
2. Discount precedence: manual discount vs referral discount (manual precedence vs referral precedence vs best_for_patient).
3. RBAC permission enforcement: requiring 'billing.discount' for manual discounts and unauthorized rejection.
4. Cap enforcement: price list item max_discount_pct and override requires override_reason.
5. Invoice-level discount recalculation (`apply_discount_to_invoice`) and audit log emission (`discount.applied`).
6. Multi-tenant isolation for referral rules and discount applications.
"""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
from sqlalchemy.orm import Session

from app.audit.service import get_audit_logs
from app.billing.discount_service import (
    calculate_line_discount,
    resolve_referral_rule,
    apply_discount_to_invoice,
)
from app.billing.invoice_service import create_invoice
from app.errors import ForbiddenError, NotFoundError, ValidationError, ConflictError
from app.models.billing import Invoice, PriceList, PriceListItem, ReferralPartner, ReferralRule
from app.models.core import Tenant, Branch
from app.models.identity import Permission, Role, RolePermission, User, UserRole
from app.models.pathology import Test
from app.models.patient import Patient
from app.security.tenant_guard import TenantContext

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db import Base


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




def _setup_discount_env(db_session: Session):
    tenant = Tenant(name="Discount Hospital", code="DISC-01")
    db_session.add(tenant)
    db_session.flush()

    branch = Branch(tenant_id=tenant.id, name="Main Wing", code="MAIN")
    db_session.add(branch)

    perm = db_session.query(Permission).filter(Permission.code == "billing.discount").first()
    if not perm:
        perm = Permission(code="billing.discount", module="billing", resource="invoice", action="discount")
        db_session.add(perm)
        db_session.flush()

    role_clerk = Role(tenant_id=tenant.id, name="Billing Clerk")
    role_guest = Role(tenant_id=tenant.id, name="Guest Staff")
    db_session.add_all([role_clerk, role_guest])
    db_session.flush()

    db_session.add(RolePermission(role_id=role_clerk.id, permission_id=perm.id))
    db_session.flush()

    user_clerk = User(tenant_id=tenant.id, username="clerk1", email="clerk@disc.org", hashed_password="pw")
    user_guest = User(tenant_id=tenant.id, username="guest1", email="guest@disc.org", hashed_password="pw")
    db_session.add_all([user_clerk, user_guest])
    db_session.flush()

    db_session.add(UserRole(user_id=user_clerk.id, role_id=role_clerk.id))
    db_session.add(UserRole(user_id=user_guest.id, role_id=role_guest.id))

    patient = Patient(
        tenant_id=tenant.id,
        patient_no="P-10001",
        first_name="Alice",
        last_name="Wonder",
        sex="female",
    )
    test1 = Test(tenant_id=tenant.id, code="CBC", name="Complete Blood Count", display_name="CBC")
    test2 = Test(tenant_id=tenant.id, code="LIPID", name="Lipid Panel", display_name="Lipid Panel")
    db_session.add_all([patient, test1, test2])
    db_session.flush()

    partner = ReferralPartner(
        tenant_id=tenant.id,
        partner_type="doctor",
        name="Dr. Gregory House",
        status="active",
    )
    db_session.add(partner)
    db_session.flush()

    plist = PriceList(
        tenant_id=tenant.id,
        code="STD",
        name="Standard Rates",
        is_default=True,
        effective_from=datetime.now(timezone.utc) - timedelta(days=5),
    )
    db_session.add(plist)
    db_session.flush()

    pli1 = PriceListItem(
        tenant_id=tenant.id,
        price_list_id=plist.id,
        item_type="test",
        item_id=test1.id,
        rate=50.0,
        max_discount_pct=15.0,
    )
    db_session.add(pli1)
    db_session.flush()

    return {
        "tenant": tenant,
        "branch": branch,
        "clerk": user_clerk,
        "guest": user_guest,
        "patient": patient,
        "test1": test1,
        "test2": test2,
        "partner": partner,
        "ctx": TenantContext(tenant_id=tenant.id, user_id=user_clerk.id, branch_id=branch.id),
    }



def test_referral_rule_precedence_and_matching(db_session: Session):
    env = _setup_discount_env(db_session)
    tenant_id = env["tenant"].id
    partner_id = env["partner"].id
    now = datetime.now(timezone.utc)

    r_global = ReferralRule(
        tenant_id=tenant_id,
        partner_id=partner_id,
        scope_type="all",
        effective_from=now - timedelta(days=1),
        patient_discount_pct=10.0,
        priority=100,
    )
    dept_id = "d1111111-1111-1111-1111-111111111111"
    r_dept = ReferralRule(
        tenant_id=tenant_id,
        partner_id=partner_id,
        scope_type="department",
        scope_id=dept_id,
        effective_from=now - timedelta(days=1),
        patient_discount_pct=15.0,
        priority=50,
    )
    r_test = ReferralRule(
        tenant_id=tenant_id,
        partner_id=partner_id,
        scope_type="test",
        scope_id=env["test1"].id,
        effective_from=now - timedelta(days=1),
        patient_discount_pct=25.0,
        priority=10,
    )
    db_session.add_all([r_global, r_dept, r_test])
    db_session.flush()

    matched = resolve_referral_rule(
        db_session,
        tenant_id=tenant_id,
        partner_id=partner_id,
        item_type="test",
        item_id=env["test1"].id,
        department_id=dept_id,
    )
    assert matched is not None
    assert matched.id == r_test.id
    assert float(matched.patient_discount_pct) == 25.0

    matched_dept = resolve_referral_rule(
        db_session,
        tenant_id=tenant_id,
        partner_id=partner_id,
        item_type="test",
        item_id=env["test2"].id,
        department_id=dept_id,
    )
    assert matched_dept is not None
    assert matched_dept.id == r_dept.id
    assert float(matched_dept.patient_discount_pct) == 15.0

    matched_global = resolve_referral_rule(
        db_session,
        tenant_id=tenant_id,
        partner_id=partner_id,
        item_type="test",
        item_id=env["test2"].id,
        department_id=None,
    )
    assert matched_global is not None
    assert matched_global.id == r_global.id
    assert float(matched_global.patient_discount_pct) == 10.0


def test_discount_precedence_modes(db_session: Session):
    env = _setup_discount_env(db_session)
    tenant_id = env["tenant"].id
    partner_id = env["partner"].id
    now = datetime.now(timezone.utc)

    r = ReferralRule(
        tenant_id=tenant_id,
        partner_id=partner_id,
        scope_type="all",
        effective_from=now - timedelta(days=1),
        patient_discount_pct=10.0,
        priority=100,
    )
    db_session.add(r)
    db_session.flush()

    unit_price = Decimal("100.00")
    qty = Decimal("1.0")

    # Mode 1: manual_precedence
    res1 = calculate_line_discount(
        db_session,
        tenant_context=env["ctx"],
        unit_price=unit_price,
        qty=qty,
        referral_partner_id=partner_id,
        manual_discount_pct=Decimal("5.0"),
        discount_mode_preference="manual_precedence",
    )
    assert res1.applied_source == "manual"
    assert res1.discount_pct == Decimal("5.0")
    assert res1.discount_amount == Decimal("5.00")

    # Mode 2: best_for_patient
    res2 = calculate_line_discount(
        db_session,
        tenant_context=env["ctx"],
        unit_price=unit_price,
        qty=qty,
        referral_partner_id=partner_id,
        manual_discount_pct=Decimal("5.0"),
        discount_mode_preference="best_for_patient",
    )
    assert res2.applied_source == "referral"
    assert res2.discount_pct == Decimal("10.0")
    assert res2.discount_amount == Decimal("10.00")

    # Mode 3: referral_precedence
    res3 = calculate_line_discount(
        db_session,
        tenant_context=env["ctx"],
        unit_price=unit_price,
        qty=qty,
        referral_partner_id=partner_id,
        manual_discount_pct=Decimal("15.0"),
        discount_mode_preference="referral_precedence",
    )
    assert res3.applied_source == "referral"
    assert res3.discount_pct == Decimal("10.0")


def test_rbac_authorization_for_discounts(db_session: Session):
    env = _setup_discount_env(db_session)
    guest_ctx = TenantContext(tenant_id=env["tenant"].id, user_id=env["guest"].id)

    with pytest.raises(ForbiddenError) as exc_info:
        calculate_line_discount(
            db_session,
            tenant_context=guest_ctx,
            unit_price=Decimal("100.00"),
            qty=Decimal("1.0"),
            manual_discount_pct=Decimal("10.0"),
        )
    assert "not authorized to grant discounts" in str(exc_info.value)


def test_discount_cap_enforcement_and_override(db_session: Session):
    env = _setup_discount_env(db_session)
    unit_price = Decimal("100.00")
    qty = Decimal("1.0")

    with pytest.raises(ValidationError) as exc:
        calculate_line_discount(
            db_session,
            tenant_context=env["ctx"],
            unit_price=unit_price,
            qty=qty,
            item_type="test",
            item_id=env["test1"].id,
            manual_discount_pct=Decimal("20.0"),
        )
    assert "exceeds maximum cap" in str(exc.value)

    res = calculate_line_discount(
        db_session,
        tenant_context=env["ctx"],
        unit_price=unit_price,
        qty=qty,
        item_type="test",
        item_id=env["test1"].id,
        manual_discount_pct=Decimal("20.0"),
        override_reason="Director approved special discount for compassionate case",
    )
    assert res.applied_source == "manual"
    assert res.discount_pct == Decimal("20.0")
    assert res.override_reason is not None


def test_apply_discount_to_invoice_and_audit_event(db_session: Session):
    env = _setup_discount_env(db_session)

    inv = create_invoice(
        db_session,
        tenant_context=env["ctx"],
        patient_id=env["patient"].id,
        branch_id=env["branch"].id,
        items=[
            {"description": "Line A", "qty": 1.0, "unit_price": 60.0, "tax_rate_pct": 10.0},
            {"description": "Line B", "qty": 1.0, "unit_price": 40.0, "tax_rate_pct": 0.0},
        ],
    )
    assert float(inv.subtotal) == 100.0
    assert float(inv.discount_total) == 0.0

    updated_inv = apply_discount_to_invoice(
        db_session,
        tenant_context=env["ctx"],
        invoice_id=inv.id,
        discount_pct=10.0,
        override_reason="Holiday promo",
    )

    assert float(updated_inv.discount_total) == 10.0
    assert float(updated_inv.tax_total) == 5.40
    assert float(updated_inv.grand_total) == 95.40
    assert "Holiday promo" in (updated_inv.notes or "")

    logs = get_audit_logs(db_session, tenant_id=env["tenant"].id, action_code="discount.applied")
    assert len(logs) >= 1
    assert logs[0].entity_id == inv.id
    assert logs[0].after_json.get("discount_total") == 10.0


def test_tenant_isolation_on_discounts(db_session: Session):
    env = _setup_discount_env(db_session)

    t2 = Tenant(name="Other Hospital", code="OTHER-01")
    db_session.add(t2)
    db_session.flush()

    t2_ctx = TenantContext(tenant_id=t2.id, user_id=None)

    inv = create_invoice(
        db_session,
        tenant_context=env["ctx"],
        patient_id=env["patient"].id,
        items=[{"description": "Item", "qty": 1.0, "unit_price": 50.0}],
    )

    with pytest.raises(NotFoundError):
        apply_discount_to_invoice(
            db_session,
            tenant_context=t2_ctx,
            invoice_id=inv.id,
            discount_pct=10.0,
        )



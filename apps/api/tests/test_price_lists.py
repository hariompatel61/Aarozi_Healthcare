from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.models.core import Tenant, Branch
from app.models.pathology import Test
from app.models.billing import PriceList, PriceListItem
from app.security.tenant_guard import TenantContext
from app.errors import ConflictError, ValidationError
from app.billing.pricing_service import (
    create_price_list,
    get_price_list,
    list_price_lists,
    add_item_to_price_list,
    resolve_pricing_rate,
    PriceListNotFoundError,
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
def pricing_test_setup(db_session: Session):
    tenant = Tenant(id=str(uuid.uuid4()), name="Alpha Diagnostics", code="ALPHA", is_active=True)
    branch1 = Branch(id=str(uuid.uuid4()), tenant_id=tenant.id, name="City Center", code="CC01")
    branch2 = Branch(id=str(uuid.uuid4()), tenant_id=tenant.id, name="North Suburb", code="NS01")

    t_cbc = Test(id=str(uuid.uuid4()), tenant_id=tenant.id, code="CBC", name="Complete Blood Count", display_name="Complete Blood Count")
    t_lft = Test(id=str(uuid.uuid4()), tenant_id=tenant.id, code="LFT", name="Liver Function Test", display_name="Liver Function Test")

    db_session.add_all([tenant, branch1, branch2, t_cbc, t_lft])
    db_session.commit()

    ctx = TenantContext(tenant_id=tenant.id, branch_id=branch1.id, user_id=str(uuid.uuid4()))
    return {
        "tenant": tenant,
        "branch1": branch1,
        "branch2": branch2,
        "cbc": t_cbc,
        "lft": t_lft,
        "ctx": ctx,
    }


def test_create_and_get_price_list(db_session: Session, pricing_test_setup):
    ctx = pricing_test_setup["ctx"]
    cbc = pricing_test_setup["cbc"]

    plist = create_price_list(
        db_session,
        tenant_context=ctx,
        code="STD-2026",
        name="Standard Rates 2026",
        currency="USD",
        is_default=True,
        items=[
            {"item_type": "test", "item_id": cbc.id, "rate": 50.0, "min_rate": 40.0, "max_discount_pct": 20.0}
        ],
    )

    assert plist.id is not None
    assert plist.code == "STD-2026"
    assert plist.is_default is True
    assert len(plist.items) == 1
    assert float(plist.items[0].rate) == 50.0

    retrieved = get_price_list(db_session, tenant_context=ctx, price_list_id=plist.id)
    assert retrieved.name == "Standard Rates 2026"
    assert len(retrieved.items) == 1


def test_price_list_effective_dates(db_session: Session, pricing_test_setup):
    ctx = pricing_test_setup["ctx"]
    cbc = pricing_test_setup["cbc"]
    now = datetime.now(timezone.utc)

    expired_list = create_price_list(
        db_session,
        tenant_context=ctx,
        code="EXP-2025",
        name="Expired Rates 2025",
        is_default=False,
        effective_from=now - timedelta(days=400),
        effective_to=now - timedelta(days=35),
        items=[{"item_type": "test", "item_id": cbc.id, "rate": 30.0}],
    )

    current_list = create_price_list(
        db_session,
        tenant_context=ctx,
        code="CURR-2026",
        name="Current Rates 2026",
        is_default=True,
        effective_from=now - timedelta(days=30),
        effective_to=now + timedelta(days=335),
        items=[{"item_type": "test", "item_id": cbc.id, "rate": 45.0}],
    )

    res_today = resolve_pricing_rate(
        db_session,
        tenant_context=ctx,
        item_type="test",
        item_id=cbc.id,
        as_of=now,
    )
    assert res_today["source"] == "tenant_default"
    assert res_today["rate"] == 45.0

    res_past = resolve_pricing_rate(
        db_session,
        tenant_context=ctx,
        item_type="test",
        item_id=cbc.id,
        as_of=now - timedelta(days=100),
    )
    assert res_past["price_list_id"] == expired_list.id
    assert res_past["rate"] == 30.0


def test_branch_rate_override_hierarchy(db_session: Session, pricing_test_setup):
    ctx = pricing_test_setup["ctx"]
    branch1 = pricing_test_setup["branch1"]
    branch2 = pricing_test_setup["branch2"]
    cbc = pricing_test_setup["cbc"]

    create_price_list(
        db_session,
        tenant_context=ctx,
        code="TENANT-DEF",
        name="Tenant Default",
        is_default=True,
        items=[{"item_type": "test", "item_id": cbc.id, "rate": 50.0}],
    )

    create_price_list(
        db_session,
        tenant_context=ctx,
        branch_id=branch1.id,
        code="BRANCH-1-SPEC",
        name="Branch 1 Rates",
        items=[{"item_type": "test", "item_id": cbc.id, "rate": 65.0}],
    )

    res_b1 = resolve_pricing_rate(
        db_session,
        tenant_context=ctx,
        branch_id=branch1.id,
        item_type="test",
        item_id=cbc.id,
    )
    assert res_b1["source"] == "branch_rate"
    assert res_b1["rate"] == 65.0

    res_b2 = resolve_pricing_rate(
        db_session,
        tenant_context=ctx,
        branch_id=branch2.id,
        item_type="test",
        item_id=cbc.id,
    )
    assert res_b2["source"] == "tenant_default"
    assert res_b2["rate"] == 50.0


def test_price_list_validations_and_uniqueness(db_session: Session, pricing_test_setup):
    ctx = pricing_test_setup["ctx"]
    now = datetime.now(timezone.utc)

    with pytest.raises(ValidationError):
        create_price_list(db_session, tenant_context=ctx, code="", name="Invalid")

    with pytest.raises(ValidationError):
        create_price_list(
            db_session,
            tenant_context=ctx,
            code="INVALID-DATES",
            name="Invalid Dates",
            effective_from=now,
            effective_to=now - timedelta(days=1),
        )

    create_price_list(db_session, tenant_context=ctx, code="UNIQUE-01", name="Unique List")
    with pytest.raises(ConflictError):
        create_price_list(db_session, tenant_context=ctx, code="UNIQUE-01", name="Duplicate Code")


def test_tenant_isolation_in_price_lists(db_session: Session):
    t1 = Tenant(id=str(uuid.uuid4()), name="Tenant 1", code="T1", is_active=True)
    t2 = Tenant(id=str(uuid.uuid4()), name="Tenant 2", code="T2", is_active=True)
    db_session.add_all([t1, t2])
    db_session.commit()

    ctx1 = TenantContext(tenant_id=t1.id)
    ctx2 = TenantContext(tenant_id=t2.id)

    pl1 = create_price_list(db_session, tenant_context=ctx1, code="PL-SAME", name="T1 List")
    pl2 = create_price_list(db_session, tenant_context=ctx2, code="PL-SAME", name="T2 List")

    assert pl1.id != pl2.id

    with pytest.raises(PriceListNotFoundError):
        get_price_list(db_session, tenant_context=ctx2, price_list_id=pl1.id)

    items_t1, count_t1 = list_price_lists(db_session, tenant_context=ctx1)
    items_t2, count_t2 = list_price_lists(db_session, tenant_context=ctx2)
    assert count_t1 == 1
    assert count_t2 == 1
    assert items_t1[0].id == pl1.id
    assert items_t2[0].id == pl2.id


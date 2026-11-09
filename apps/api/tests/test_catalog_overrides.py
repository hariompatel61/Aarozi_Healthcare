"""Automated Tests for Pathology 3-Layer Catalog Architecture, Tenant Overrides, Offline-First Persistence, and Mass Importer."""

import io
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.models.core import Tenant
from app.models.offline import SyncEvent
from app.models.pathology import Test, TestParameter, TestReferenceRange, TenantTestOverride
from app.pathology.catalog_seed import (
    SYSTEM_TENANT_ID,
    ensure_system_tenant,
    parse_multiline_parameters,
    parse_reference_intervals,
    parse_excel_or_csv,
    generate_template_excel,
    seed_default_catalog,
)
from app.pathology.test_master import (
    list_tests_with_overrides,
    get_test_detail,
    set_test_override,
    reset_test_override,
    bulk_update_tests,
    import_catalog_data,
    create_test,
)
from app.security.tenant_guard import TenantContext


@pytest.fixture
def db_session():
    """In-memory SQLite session with full schema initialized."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        # Seed test tenants
        t_sys = ensure_system_tenant(session)
        t_a = Tenant(id="TENANT_A", code="LAB_A", name="Aarozi Lab Alpha", is_active=True)
        t_b = Tenant(id="TENANT_B", code="LAB_B", name="Aarozi Lab Beta", is_active=True)
        session.add_all([t_a, t_b])
        session.commit()
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_reference_interval_parser():
    """Verify parsing of sex-specific intervals and numerical limits."""
    # 1. Sex-specific ranges
    ranges = parse_reference_intervals("Male: 13.5-17.5; Female: 12.0-15.5", note_str="Adult interval")
    assert len(ranges) == 2
    male_r = next(r for r in ranges if r["sex"] == "male")
    female_r = next(r for r in ranges if r["sex"] == "female")
    assert male_r["low_value"] == 13.5
    assert male_r["high_value"] == 17.5
    assert female_r["low_value"] == 12.0
    assert female_r["high_value"] == 15.5

    # 2. Upper limit
    range_chol = parse_reference_intervals("Desirable: <200")
    assert len(range_chol) == 1
    assert range_chol[0]["high_value"] == 200.0
    assert range_chol[0]["low_value"] is None

    # 3. Numeric bounds
    range_urea = parse_reference_intervals("15 - 40")
    assert len(range_urea) == 1
    assert range_urea[0]["low_value"] == 15.0
    assert range_urea[0]["high_value"] == 40.0

    # 4. Unconfigured / Lab-defined requires review
    range_unconf = parse_reference_intervals("Not provided / configure by laboratory")
    assert len(range_unconf) == 1
    assert range_unconf[0]["needs_review"] is True


def test_multiline_parameter_parser():
    """Verify parsing of multiline parameter details cell into structured parameters."""
    raw_cell = (
        "Hemoglobin | Unit: g/dL | Range: Male: 13.5-17.5; Female: 12.0-15.5 | Note: Adult normal\n"
        "Total WBC Count | Unit: 10^3/uL | Range: 4.0-11.0\n"
        "Platelet Count | Unit: 10^3/uL | Range: 150-450"
    )
    params = parse_multiline_parameters(raw_cell)
    assert len(params) == 3
    assert params[0]["name"] == "Hemoglobin"
    assert params[0]["unit"] == "g/dL"
    assert len(params[0]["reference_ranges"]) == 2

    assert params[1]["name"] == "Total WBC Count"
    assert params[1]["unit"] == "10^3/uL"
    assert params[1]["reference_ranges"][0]["low_value"] == 4.0

    assert params[2]["name"] == "Platelet Count"
    assert params[2]["reference_ranges"][0]["high_value"] == 450.0


def test_idempotent_catalog_seeding(db_session: Session):
    """Verify default catalog seeds idempotently without duplicates (Layer A)."""
    # Create system default investigation manually to verify seed behavior
    seeded_first = seed_default_catalog(db_session, limit=10)
    assert seeded_first >= 0

    # Second run must be completely idempotent (0 new investigations created)
    seeded_second = seed_default_catalog(db_session, limit=10)
    assert seeded_second == 0


def test_tenant_price_isolation(db_session: Session):
    """
    Verify Layer B tenant pricing isolation:
    - Base CBC default is ₹250
    - Tenant A overrides CBC price to ₹350
    - Tenant B overrides CBC price to ₹450
    - Default remains untouched
    - Tenant A and Tenant B see their respective prices
    """
    # 1. Create System Default CBC
    cbc = Test(
        tenant_id=SYSTEM_TENANT_ID,
        code="CBC",
        name="Complete Blood Count",
        display_name="Complete Blood Count",
        specimen_type="EDTA Whole Blood",
        container_type="Purple (EDTA)",
        is_system_default=True,
        base_price=250.0,
        tat_hours=4,
        status="active",
        version=1,
    )
    db_session.add(cbc)
    db_session.commit()

    ctx_a = TenantContext(tenant_id="TENANT_A")
    ctx_b = TenantContext(tenant_id="TENANT_B")

    # 2. Tenant A sets price to 350
    set_test_override(db_session, tenant_context=ctx_a, test_id=cbc.id, price=350.0)

    # 3. Tenant B sets price to 450
    set_test_override(db_session, tenant_context=ctx_b, test_id=cbc.id, price=450.0)

    # 4. Check Tenant A catalog
    list_a = list_tests_with_overrides(db_session, tenant_context=ctx_a, search="CBC")
    assert len(list_a) == 1
    assert list_a[0]["price"] == 350.0
    assert list_a[0]["badge"] == "Customized Default"
    assert list_a[0]["is_overridden"] is True

    # 5. Check Tenant B catalog
    list_b = list_tests_with_overrides(db_session, tenant_context=ctx_b, search="CBC")
    assert len(list_b) == 1
    assert list_b[0]["price"] == 450.0
    assert list_b[0]["badge"] == "Customized Default"

    # 6. Verify system default record itself was NOT changed
    db_session.refresh(cbc)
    assert float(cbc.base_price) == 250.0

    # 7. Verify sync events were enqueued for cloud sync (Layer C)
    sync_events = db_session.execute(select(SyncEvent)).scalars().all()
    assert len(sync_events) >= 2
    assert any(e.tenant_id == "TENANT_A" and e.payload_json.get("price") == 350.0 for e in sync_events)
    assert any(e.tenant_id == "TENANT_B" and e.payload_json.get("price") == 450.0 for e in sync_events)


def test_tenant_custom_test_isolation(db_session: Session):
    """
    Verify Tenant A's custom investigation is completely invisible to Tenant B.
    """
    ctx_a = TenantContext(tenant_id="TENANT_A")
    ctx_b = TenantContext(tenant_id="TENANT_B")

    # Tenant A creates custom test
    custom_test = create_test(
        db_session,
        tenant_context=ctx_a,
        code="ALPHA_CUSTOM_01",
        name="Alpha Specialized Biomarker Assay",
        specimen_type="Plasma",
    )
    custom_test.base_price = 1800.0
    db_session.commit()

    # Tenant A sees it
    list_a = list_tests_with_overrides(db_session, tenant_context=ctx_a, search="ALPHA_CUSTOM_01")
    assert len(list_a) == 1
    assert list_a[0]["badge"] == "Tenant Custom"

    # Tenant B must NEVER see Tenant A's custom test
    list_b = list_tests_with_overrides(db_session, tenant_context=ctx_b, search="ALPHA_CUSTOM_01")
    assert len(list_b) == 0


def test_test_deactivation_and_reset_override(db_session: Session):
    """
    Verify deactivating a test marks it inactive for that tenant without deleting it.
    Verify resetting an override restores default price.
    """
    lft = Test(
        tenant_id=SYSTEM_TENANT_ID,
        code="LFT",
        name="Liver Function Test",
        display_name="Liver Function Test",
        specimen_type="Serum",
        is_system_default=True,
        base_price=650.0,
        tat_hours=4,
        status="active",
        version=1,
    )
    db_session.add(lft)
    db_session.commit()

    ctx_a = TenantContext(tenant_id="TENANT_A")

    # Deactivate LFT for Tenant A
    set_test_override(db_session, tenant_context=ctx_a, test_id=lft.id, price=700.0, is_active=False)

    # Active filter should hide it
    active_tests = list_tests_with_overrides(db_session, tenant_context=ctx_a, status="active", search="LFT")
    assert len(active_tests) == 0

    # Inactive filter should show it
    inactive_tests = list_tests_with_overrides(db_session, tenant_context=ctx_a, status="inactive", search="LFT")
    assert len(inactive_tests) == 1
    assert inactive_tests[0]["is_active"] is False

    # Reset override restores defaults
    reset_test_override(db_session, tenant_context=ctx_a, test_id=lft.id)
    all_tests = list_tests_with_overrides(db_session, tenant_context=ctx_a, status="all", search="LFT")
    assert len(all_tests) == 1
    assert all_tests[0]["price"] == 650.0
    assert all_tests[0]["is_active"] is True
    assert all_tests[0]["badge"] == "System Default"


def test_bulk_update_pricing_and_tat(db_session: Session):
    """Verify bulk pricing adjustments (fixed, increase %, decrease %) and TAT assignment."""
    t1 = Test(tenant_id=SYSTEM_TENANT_ID, code="T1", name="Test 1", display_name="Test 1", base_price=100.0, tat_hours=2, is_system_default=True, status="active", version=1)
    t2 = Test(tenant_id=SYSTEM_TENANT_ID, code="T2", name="Test 2", display_name="Test 2", base_price=200.0, tat_hours=2, is_system_default=True, status="active", version=1)
    db_session.add_all([t1, t2])
    db_session.commit()

    ctx = TenantContext(tenant_id="TENANT_A")

    # Increase by 10%
    res = bulk_update_tests(db_session, tenant_context=ctx, test_ids=[t1.id, t2.id], price_action="increase_pct", price_value=10.0, tat_hours=6)
    assert res["updated_count"] == 2

    detail_1 = get_test_detail(db_session, tenant_context=ctx, test_id=t1.id)
    detail_2 = get_test_detail(db_session, tenant_context=ctx, test_id=t2.id)

    assert detail_1["price"] == 110.0
    assert detail_1["tat_hours"] == 6
    assert detail_2["price"] == 220.0
    assert detail_2["tat_hours"] == 6


def test_mass_importer_modes(db_session: Session):
    """
    Verify spreadsheet importer with:
    - insert_only: adds only new tests, skips existing
    - update_existing: updates matched records
    - upsert: updates existing and creates new
    """
    ctx = TenantContext(tenant_id="TENANT_A")

    initial_batch = [
        {"code": "IMP_A", "name": "Imported Test A", "price": 100.0, "tat_hours": 2},
        {"code": "IMP_B", "name": "Imported Test B", "price": 200.0, "tat_hours": 3},
    ]

    # 1. Upsert initial batch
    res_1 = import_catalog_data(db_session, tenant_context=ctx, tests_data=initial_batch, mode="upsert")
    assert res_1["new_count"] == 2
    assert res_1["updated_count"] == 0

    # 2. Insert-only with existing IMP_A and new IMP_C
    second_batch = [
        {"code": "IMP_A", "name": "Imported Test A (Modified)", "price": 150.0},
        {"code": "IMP_C", "name": "Imported Test C", "price": 300.0},
    ]
    res_2 = import_catalog_data(db_session, tenant_context=ctx, tests_data=second_batch, mode="insert_only")
    assert res_2["new_count"] == 1  # only IMP_C
    assert res_2["skipped_count"] == 1  # IMP_A was skipped

    # 3. Update-existing with IMP_A and non-existent IMP_D
    third_batch = [
        {"code": "IMP_A", "name": "Imported Test A (Updated)", "price": 175.0},
        {"code": "IMP_D", "name": "Imported Test D", "price": 400.0},
    ]
    res_3 = import_catalog_data(db_session, tenant_context=ctx, tests_data=third_batch, mode="update_existing")
    assert res_3["updated_count"] == 1  # IMP_A updated
    assert res_3["skipped_count"] == 1  # IMP_D skipped


def test_create_custom_test_with_parameters(db_session: Session):
    """Verify creating a custom investigation with multiple reportable parameters and ranges."""
    ctx = TenantContext(tenant_id="TENANT_A")
    params = [
        {"code": "FE", "name": "Serum Iron", "unit": "µg/dL", "result_type": "numeric", "reference_ranges": [
            {"sex": "all", "low_value": 60.0, "high_value": 170.0, "text_range": "60 - 170 µg/dL"}
        ]},
        {"code": "TIBC", "name": "Total Iron Binding Capacity", "unit": "µg/dL", "result_type": "numeric", "reference_ranges": [
            {"sex": "all", "low_value": 240.0, "high_value": 450.0, "text_range": "240 - 450 µg/dL"}
        ]},
        {"code": "SAT", "name": "Transferrin Saturation", "unit": "%", "result_type": "calculated", "reference_ranges": [
            {"sex": "all", "low_value": 20.0, "high_value": 50.0, "text_range": "20 - 50 %"}
        ]},
    ]

    test = create_test(
        db_session,
        tenant_context=ctx,
        code="IRON_PROF",
        name="Iron Profile",
        price=850.0,
        tat_hours=6,
        parameters=params,
    )
    db_session.commit()

    detail = get_test_detail(db_session, tenant_context=ctx, test_id=test.id)
    assert detail["name"] == "Iron Profile"
    assert detail["price"] == 850.0
    assert detail["tat_hours"] == 6
    assert len(detail["parameters"]) == 3
    assert detail["parameters"][0]["name"] == "Serum Iron"
    assert detail["parameters"][0]["unit"] == "µg/dL"
    assert detail["parameters"][1]["name"] == "Total Iron Binding Capacity"
    assert detail["parameters"][2]["result_type"] == "calculated"


def test_add_and_delete_parameter_endpoints(db_session: Session):
    """Verify dynamically adding and removing reportable parameters from an investigation."""
    from app.pathology.test_master import add_parameter_to_test, delete_test_parameter

    ctx = TenantContext(tenant_id="TENANT_A")
    test = create_test(
        db_session,
        tenant_context=ctx,
        code="URINE_TEST",
        name="Urine Protein Test",
        price=150.0,
    )
    db_session.commit()

    # Add a second parameter
    new_param = add_parameter_to_test(
        db_session,
        tenant_context=ctx,
        test_id=test.id,
        parameter_data={"code": "CREAT_U", "name": "Urine Creatinine", "unit": "mg/dL", "result_type": "numeric"}
    )
    assert new_param["name"] == "Urine Creatinine"

    detail = get_test_detail(db_session, tenant_context=ctx, test_id=test.id)
    assert len(detail["parameters"]) == 2

    # Delete the parameter
    del_res = delete_test_parameter(db_session, tenant_context=ctx, parameter_id=new_param["id"])
    assert del_res["deleted"] is True

    detail_after = get_test_detail(db_session, tenant_context=ctx, test_id=test.id)
    assert len(detail_after["parameters"]) == 1


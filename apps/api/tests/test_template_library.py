"""Tests for P06-07: Starter Template Library (100+ Diagnostic Templates, Schema Compliance, Seeding, Search)."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.audit.service import get_audit_logs
from app.db import Base
from app.models.core import Tenant
from app.models.reporting import ReportTemplate
from app.reporting.template_library import (
    STARTER_TEMPLATES_METADATA,
    get_starter_template_library,
    search_template_library,
    seed_starter_templates,
)
from app.reporting.template_service import validate_template_schema
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


def test_starter_template_library_count_and_disciplines():
    # Must provide 100+ distinct clinical diagnostic templates
    library = get_starter_template_library()
    assert len(library) >= 100, f"Expected at least 100 starter templates, got {len(library)}"
    assert len(STARTER_TEMPLATES_METADATA) >= 100

    categories = {t["category"] for t in library}
    assert "biochemistry" in categories
    assert "hematology" in categories
    assert "immunology" in categories
    assert "microbiology" in categories
    assert "blood_bank" in categories
    assert "general" in categories


def test_all_100_plus_templates_are_schema_compliant():
    library = get_starter_template_library()
    # Validate each template against frozen JSON schema
    for tpl in library:
        validate_template_schema(tpl)


def test_idempotent_database_seeding(db_session: Session):
    tenant = Tenant(name="National Diagnostic Lab", code="NDL-01", is_active=True)
    db_session.add(tenant)
    db_session.flush()

    ctx = TenantContext(tenant_id=tenant.id)

    # 1. First run seeds all 100+ templates
    first_count = seed_starter_templates(db_session, tenant_context=ctx, is_global=True)
    assert first_count >= 100

    # 2. Second run is idempotent (seeds 0 new templates)
    second_count = seed_starter_templates(db_session, tenant_context=ctx, is_global=True)
    assert second_count == 0

    # Verify audit log
    logs = get_audit_logs(db_session, tenant_id=tenant.id, entity_type="report_template")
    assert any(l.action_code == "report_template.library_seeded" for l in logs)


def test_search_and_pagination_in_library():
    # 1. Category search
    hem_items, hem_count = search_template_library(category="hematology", page_size=50)
    assert hem_count >= 15
    assert all(it["category"] == "hematology" for it in hem_items)

    # 2. Text search
    lipid_items, lipid_count = search_template_library(search="Lipid", page_size=10)
    assert lipid_count >= 1
    assert any("Lipid" in it["name"] for it in lipid_items)

    # 3. Bounded pagination
    p1, total = search_template_library(page=1, page_size=10)
    assert len(p1) == 10
    assert total >= 100

    p2, _ = search_template_library(page=2, page_size=10)
    assert len(p2) == 10
    assert p1[0]["code"] != p2[0]["code"]

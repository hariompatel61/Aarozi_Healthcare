"""Test Master service for Pathology: tests, specimens, methods, units, reference ranges, and active versioning."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.audit.service import log_audit_event
from app.errors import ConflictError, NotFoundError, ValidationError
from app.models.pathology import Test, TestReferenceRange
from app.security.tenant_guard import TenantContext, verify_tenant_boundary


def create_test(
    db: Session,
    *,
    tenant_context: TenantContext,
    code: str,
    name: str,
    display_name: str | None = None,
    short_name: str | None = None,
    department_id: str | None = None,
    specimen_type: str | None = None,
    container_type: str | None = None,
    method: str | None = None,
    unit: str | None = None,
    decimal_precision: int = 2,
    analyzer_code: str | None = None,
    loinc_code: str | None = None,
    calculation_formula: str | None = None,
    is_calculated: bool = False,
    reference_ranges: list[dict[str, Any]] | None = None,
    actor_user_id: str | None = None,
) -> Test:
    """Create a new Test definition in the Test Master."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id

    clean_code = (code or "").strip().upper()
    if not clean_code:
        raise ValidationError("Test code cannot be empty", field="code")
    clean_name = (name or "").strip()
    if not clean_name:
        raise ValidationError("Test name cannot be empty", field="name")
    clean_display = (display_name or clean_name).strip()

    # Check uniqueness of active code in tenant
    existing = db.execute(
        select(Test).where(
            Test.tenant_id == tenant_id,
            Test.code == clean_code,
            Test.status == "active",
        )
    ).scalars().first()
    if existing:
        raise ConflictError(f"Active test with code '{clean_code}' already exists (ID: {existing.id})")

    test = Test(
        tenant_id=tenant_id,
        department_id=department_id,
        code=clean_code,
        name=clean_name,
        display_name=clean_display,
        short_name=short_name.strip() if short_name else None,
        specimen_type=specimen_type.strip() if specimen_type else None,
        container_type=container_type.strip() if container_type else None,
        method=method.strip() if method else None,
        unit=unit.strip() if unit else None,
        decimal_precision=max(0, decimal_precision),
        analyzer_code=analyzer_code.strip() if analyzer_code else None,
        loinc_code=loinc_code.strip() if loinc_code else None,
        calculation_formula=calculation_formula.strip() if calculation_formula else None,
        is_calculated=is_calculated or bool(calculation_formula),
        version=1,
        status="active",
    )
    db.add(test)
    db.flush()

    if reference_ranges:
        for rr in reference_ranges:
            ref_range = TestReferenceRange(
                test_id=test.id,
                sex=rr.get("sex", "all"),
                age_min=rr.get("age_min"),
                age_max=rr.get("age_max"),
                low_value=rr.get("low_value"),
                high_value=rr.get("high_value"),
                critical_low=rr.get("critical_low"),
                critical_high=rr.get("critical_high"),
                text_range=rr.get("text_range"),
            )
            db.add(ref_range)

    log_audit_event(
        db,
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        action_code="test.create",
        entity_type="test",
        entity_id=test.id,
        before_json=None,
        after_json={
            "code": test.code,
            "name": test.name,
            "specimen_type": test.specimen_type,
            "unit": test.unit,
            "version": test.version,
            "status": test.status,
        },
    )

    db.flush()
    return test
def get_test(
    db: Session,
    *,
    tenant_context: TenantContext,
    test_id: str,
) -> Test:
    """Get test by ID within tenant boundary."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id

    stmt = (
        select(Test)
        .options(joinedload(Test.reference_ranges))
        .where(Test.id == test_id, Test.tenant_id == tenant_id)
    )
    test = db.execute(stmt).unique().scalar_one_or_none()
    if not test:
        raise NotFoundError(f"Test with ID '{test_id}' not found", field="test_id")
    return test


def get_active_test_by_code(
    db: Session,
    *,
    tenant_context: TenantContext,
    code: str,
) -> Test:
    """Get active version of test by code within tenant boundary."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id
    clean_code = (code or "").strip().upper()

    stmt = (
        select(Test)
        .options(joinedload(Test.reference_ranges))
        .where(Test.tenant_id == tenant_id, Test.code == clean_code, Test.status == "active")
    )
    test = db.execute(stmt).unique().scalar_one_or_none()
    if not test:
        raise NotFoundError(f"Active test with code '{clean_code}' not found", field="code")
    return test

def create_new_test_version(
    db: Session,
    *,
    tenant_context: TenantContext,
    test_id: str,
    update_data: dict[str, Any],
    actor_user_id: str | None = None,
    reason: str | None = None,
) -> Test:
    """Create a new version of an existing test and mark previous version superseded."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id

    current_test = get_test(db, tenant_context=tenant_context, test_id=test_id)
    if current_test.status != "active":
        raise ConflictError(f"Cannot version non-active test '{current_test.code}' (current status: {current_test.status})")

    now = datetime.now(timezone.utc)
    current_test.status = "superseded"
    current_test.effective_to = now

    new_version_num = current_test.version + 1

    new_test = Test(
        tenant_id=tenant_id,
        department_id=update_data.get("department_id", current_test.department_id),
        code=current_test.code,
        name=update_data.get("name", current_test.name),
        display_name=update_data.get("display_name", current_test.display_name),
        short_name=update_data.get("short_name", current_test.short_name),
        specimen_type=update_data.get("specimen_type", current_test.specimen_type),
        container_type=update_data.get("container_type", current_test.container_type),
        method=update_data.get("method", current_test.method),
        unit=update_data.get("unit", current_test.unit),
        decimal_precision=update_data.get("decimal_precision", current_test.decimal_precision),
        analyzer_code=update_data.get("analyzer_code", current_test.analyzer_code),
        loinc_code=update_data.get("loinc_code", current_test.loinc_code),
        calculation_formula=update_data.get("calculation_formula", current_test.calculation_formula),
        is_calculated=update_data.get("is_calculated", current_test.is_calculated),
        version=new_version_num,
        status="active",
        effective_from=now,
    )
    db.add(new_test)
    db.flush()

    new_ranges = update_data.get("reference_ranges")
    if new_ranges is not None:
        for rr in new_ranges:
            ref_range = TestReferenceRange(
                test_id=new_test.id,
                sex=rr.get("sex", "all"),
                age_min=rr.get("age_min"),
                age_max=rr.get("age_max"),
                low_value=rr.get("low_value"),
                high_value=rr.get("high_value"),
                critical_low=rr.get("critical_low"),
                critical_high=rr.get("critical_high"),
                text_range=rr.get("text_range"),
            )
            db.add(ref_range)
    else:
        for rr in current_test.reference_ranges:
            ref_range = TestReferenceRange(
                test_id=new_test.id,
                sex=rr.sex,
                age_min=rr.age_min,
                age_max=rr.age_max,
                low_value=rr.low_value,
                high_value=rr.high_value,
                critical_low=rr.critical_low,
                critical_high=rr.critical_high,
                text_range=rr.text_range,
            )
            db.add(ref_range)

    log_audit_event(
        db,
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        action_code="test.version",
        entity_type="test",
        entity_id=new_test.id,
        before_json={"id": current_test.id, "version": current_test.version, "status": "superseded"},
        after_json={
            "id": new_test.id,
            "version": new_test.version,
            "status": "active",
            "reason": reason or "Clinical test definition updated",
        },
    )

    db.flush()
    return new_test


def list_tests(
    db: Session,
    *,
    tenant_context: TenantContext,
    status: str | None = "active",
    search: str | None = None,
    department_id: str | None = None,
    specimen_type: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[Test]:
    """List tests bounded to tenant with pagination."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id

    limit = min(max(1, limit), 50)
    offset = max(0, offset)

    stmt = (
        select(Test)
        .options(joinedload(Test.reference_ranges))
        .where(Test.tenant_id == tenant_id)
    )

    if status:
        stmt = stmt.where(Test.status == status)

    if department_id:
        stmt = stmt.where(Test.department_id == department_id)

    if specimen_type:
        stmt = stmt.where(Test.specimen_type == specimen_type)

    if search:
        search_term = f"%{search.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Test.code).like(search_term),
                func.lower(Test.name).like(search_term),
                func.lower(Test.display_name).like(search_term),
            )
        )

    stmt = stmt.order_by(Test.code.asc(), Test.version.desc()).limit(limit).offset(offset)
    return list(db.execute(stmt).unique().scalars().all())


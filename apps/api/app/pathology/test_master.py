"""Test Master service for Pathology: tests, specimens, methods, units, reference ranges, and active versioning."""
from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

import uuid
from app.audit.service import log_audit_event
from app.errors import ConflictError, NotFoundError, ValidationError
from app.models.pathology import Test, TestReferenceRange, TenantTestOverride, TestParameter
from app.security.tenant_guard import TenantContext, verify_tenant_boundary
from app.sync.service import enqueue_sync_event


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
    price: float = 250.0,
    tat_hours: int = 4,
    reference_ranges: list[dict[str, Any]] | None = None,
    parameters: list[dict[str, Any]] | None = None,
    actor_user_id: str | None = None,
) -> Test:
    """Create a new Test definition in the Test Master with reportable parameters."""
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
        specimen_type=specimen_type.strip() if specimen_type else "Blood",
        container_type=container_type.strip() if container_type else "Serum Separator",
        method=method.strip() if method else None,
        unit=unit.strip() if unit else "Var",
        decimal_precision=max(0, decimal_precision),
        analyzer_code=analyzer_code.strip() if analyzer_code else None,
        loinc_code=loinc_code.strip() if loinc_code else None,
        calculation_formula=calculation_formula.strip() if calculation_formula else None,
        is_calculated=is_calculated or bool(calculation_formula),
        base_price=price,
        tat_hours=tat_hours,
        is_system_default=False,
        version=1,
        status="active",
    )
    db.add(test)
    db.flush()

    # Process Parameters
    param_names = []
    if parameters and len(parameters) > 0:
        for p_idx, p in enumerate(parameters, start=1):
            p_code = (p.get("code") or f"{clean_code}_{p_idx}").strip().upper()
            p_name = (p.get("name") or p_code).strip()
            param_names.append(p_name)
            param = TestParameter(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                test_id=test.id,
                code=p_code[:64],
                name=p_name,
                unit=p.get("unit"),
                result_type=p.get("result_type", "numeric"),
                sort_order=p_idx,
                is_active=p.get("is_active", True),
            )
            db.add(param)
            db.flush()

            p_ranges = p.get("reference_ranges") or []
            if p_ranges:
                for r in p_ranges:
                    ref_range = TestReferenceRange(
                        id=str(uuid.uuid4()),
                        test_id=test.id,
                        parameter_id=param.id,
                        tenant_id=tenant_id,
                        sex=r.get("sex", "all"),
                        age_unit="years",
                        priority=1,
                        low_value=r.get("low_value"),
                        high_value=r.get("high_value"),
                        critical_low=r.get("critical_low"),
                        critical_high=r.get("critical_high"),
                        text_range=r.get("text_range"),
                    )
                    db.add(ref_range)
            else:
                # Add default reference range
                ref_range = TestReferenceRange(
                    id=str(uuid.uuid4()),
                    test_id=test.id,
                    parameter_id=param.id,
                    tenant_id=tenant_id,
                    sex="all",
                    age_unit="years",
                    priority=1,
                    text_range="Refer to standard laboratory reference intervals",
                )
                db.add(ref_range)
    else:
        # Default single parameter matching test name
        param_names.append(clean_name)
        param = TestParameter(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            test_id=test.id,
            code=clean_code[:64],
            name=clean_name,
            unit=unit,
            result_type="numeric",
            sort_order=1,
            is_active=True,
        )
        db.add(param)
        db.flush()

        if reference_ranges:
            for rr in reference_ranges:
                ref_range = TestReferenceRange(
                    id=str(uuid.uuid4()),
                    test_id=test.id,
                    parameter_id=param.id,
                    tenant_id=tenant_id,
                    sex=rr.get("sex", "all"),
                    age_unit="years",
                    priority=1,
                    low_value=rr.get("low_value"),
                    high_value=rr.get("high_value"),
                    critical_low=rr.get("critical_low"),
                    critical_high=rr.get("critical_high"),
                    text_range=rr.get("text_range"),
                )
                db.add(ref_range)
        else:
            ref_range = TestReferenceRange(
                id=str(uuid.uuid4()),
                test_id=test.id,
                parameter_id=param.id,
                tenant_id=tenant_id,
                sex="all",
                age_unit="years",
                priority=1,
                text_range="Refer to standard laboratory reference intervals",
            )
            db.add(ref_range)

    test.parameters_summary = ", ".join(param_names[:5]) + (f" (+{len(param_names)-5} more)" if len(param_names) > 5 else "")

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
            "parameters_count": len(param_names),
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


def list_tests_with_overrides(
    db: Session,
    *,
    tenant_context: TenantContext,
    status: str | None = "all",
    search: str | None = None,
    department_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """
    List tests resolving Layer A (System Default) and Layer B (Tenant Override).
    Tenant-specific prices, TAT, custom names, and active/inactive status override defaults.
    Tenant custom tests are isolated to this tenant.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id

    # 1. Fetch system tests and this tenant's custom tests
    stmt = (
        select(Test)
        .options(
            joinedload(Test.reference_ranges),
            joinedload(Test.parameters),
        )
        .where(
            or_(
                Test.tenant_id == tenant_id,
                Test.is_system_default == True,  # noqa: E712
            )
        )
    )

    if department_id:
        stmt = stmt.where(Test.department_id == department_id)

    raw_tests = list(db.execute(stmt).unique().scalars().all())

    # 2. Fetch tenant overrides
    ov_stmt = select(TenantTestOverride).where(TenantTestOverride.tenant_id == tenant_id)
    overrides_list = list(db.execute(ov_stmt).scalars().all())
    overrides_by_test_id = {ov.test_id: ov for ov in overrides_list}

    # 3. Merge system defaults and tenant overrides
    results = []
    search_lower = (search or "").strip().lower()

    for t in raw_tests:
        ov = overrides_by_test_id.get(t.id)

        effective_price = float(ov.price) if (ov and ov.price is not None) else float(t.base_price or 0.0)
        effective_tat = ov.tat_hours if (ov and ov.tat_hours is not None) else (t.tat_hours or 4)
        is_active = ov.is_active if ov else (t.status == "active")
        effective_name = ov.custom_name if (ov and ov.custom_name) else (t.display_name or t.name)
        effective_code = ov.custom_code if (ov and ov.custom_code) else t.code
        effective_specimen = ov.specimen_type if (ov and ov.specimen_type) else (t.specimen_type or "Serum")
        effective_container = ov.container_type if (ov and ov.container_type) else (t.container_type or "Red (Plain / Gel)")
        sync_status = ov.sync_status if ov else "synced"
        is_overridden = bool(ov)

        if t.is_system_default:
            badge = "Customized Default" if is_overridden else "System Default"
        else:
            badge = "Tenant Custom"

        # Apply status filter
        if status == "active" and not is_active:
            continue
        elif status == "inactive" and is_active:
            continue

        # Apply search filter
        if search_lower:
            matches_search = (
                search_lower in effective_code.lower()
                or search_lower in effective_name.lower()
                or (t.specimen_type and search_lower in t.specimen_type.lower())
                or (t.parameters_summary and search_lower in t.parameters_summary.lower())
            )
            if not matches_search:
                continue

        # Format parameter summaries
        ref_ranges_list = [
            {
                "id": r.id,
                "sex": r.sex,
                "low_value": float(r.low_value) if r.low_value is not None else None,
                "high_value": float(r.high_value) if r.high_value is not None else None,
                "critical_low": float(r.critical_low) if r.critical_low is not None else None,
                "critical_high": float(r.critical_high) if r.critical_high is not None else None,
                "text_range": r.text_range,
                "notes": r.notes,
                "needs_review": r.needs_review,
            }
            for r in (t.reference_ranges or [])
        ]

        parameters_list = [
            {
                "id": p.id,
                "code": p.code,
                "name": p.name,
                "unit": p.unit,
                "result_type": p.result_type,
                "sort_order": p.sort_order,
                "is_active": p.is_active,
            }
            for p in (t.parameters or [])
        ]

        results.append(
            {
                "id": t.id,
                "code": effective_code,
                "name": effective_name,
                "default_name": t.name,
                "default_code": t.code,
                "department": "Hematology" if "edta" in effective_specimen.lower() else ("Coagulation" if "citrate" in effective_specimen.lower() else "Biochemistry"),
                "specimen": effective_specimen,
                "tube_color": effective_container,
                "unit": t.unit or "Var",
                "tat_hours": effective_tat,
                "price": effective_price,
                "default_price": float(t.base_price or 0.0),
                "is_active": is_active,
                "is_system_default": t.is_system_default,
                "is_overridden": is_overridden,
                "badge": badge,
                "sync_status": sync_status,
                "parameters_summary": t.parameters_summary or (", ".join(p["name"] for p in parameters_list) if parameters_list else ""),
                "parameters_count": len(parameters_list),
                "parameters": parameters_list,
                "reference_ranges": ref_ranges_list,
            }
        )

    # Sort: prioritized by code
    results.sort(key=lambda x: (0 if x["is_overridden"] else 1, x["code"]))
    return results[offset : offset + limit]


def get_test_detail(
    db: Session,
    *,
    tenant_context: TenantContext,
    test_id: str,
) -> dict[str, Any]:
    """Retrieve full test details, parameters, reference intervals, and override status."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id

    test = db.execute(
        select(Test)
        .options(
            joinedload(Test.reference_ranges),
            joinedload(Test.parameters).joinedload(TestParameter.reference_ranges),
        )
        .where(
            Test.id == test_id,
            or_(
                Test.tenant_id == tenant_id,
                Test.is_system_default == True,  # noqa: E712
            ),
        )
    ).unique().scalar_one_or_none()

    if not test:
        raise NotFoundError(f"Investigation '{test_id}' not found.")

    override = db.execute(
        select(TenantTestOverride).where(
            TenantTestOverride.tenant_id == tenant_id,
            TenantTestOverride.test_id == test_id,
        )
    ).scalar_one_or_none()

    effective_price = float(override.price) if (override and override.price is not None) else float(test.base_price or 0.0)
    effective_tat = override.tat_hours if (override and override.tat_hours is not None) else (test.tat_hours or 4)
    is_active = override.is_active if override else (test.status == "active")
    effective_name = override.custom_name if (override and override.custom_name) else (test.display_name or test.name)
    effective_code = override.custom_code if (override and override.custom_code) else test.code
    sync_status = override.sync_status if override else "synced"

    parameters = []
    for p in (test.parameters or []):
        param_ranges = [
            {
                "id": r.id,
                "sex": r.sex,
                "low_value": float(r.low_value) if r.low_value is not None else None,
                "high_value": float(r.high_value) if r.high_value is not None else None,
                "critical_low": float(r.critical_low) if r.critical_low is not None else None,
                "critical_high": float(r.critical_high) if r.critical_high is not None else None,
                "text_range": r.text_range,
                "notes": r.notes,
                "needs_review": r.needs_review,
            }
            for r in (p.reference_ranges or [])
        ]
        parameters.append(
            {
                "id": p.id,
                "code": p.code,
                "name": p.name,
                "unit": p.unit,
                "result_type": p.result_type,
                "sort_order": p.sort_order,
                "is_active": p.is_active,
                "validation_rules": p.validation_rules,
                "reference_ranges": param_ranges,
            }
        )

    return {
        "id": test.id,
        "code": effective_code,
        "name": effective_name,
        "default_code": test.code,
        "default_name": test.name,
        "department": "Biochemistry",
        "specimen": test.specimen_type or "Serum",
        "tube_color": test.container_type or "Red (Plain / Gel)",
        "unit": test.unit or "Var",
        "price": effective_price,
        "default_price": float(test.base_price or 0.0),
        "tat_hours": effective_tat,
        "default_tat_hours": test.tat_hours or 4,
        "is_active": is_active,
        "is_system_default": test.is_system_default,
        "is_overridden": bool(override),
        "badge": "Customized Default" if (test.is_system_default and override) else ("System Default" if test.is_system_default else "Tenant Custom"),
        "sync_status": sync_status,
        "parameters": parameters,
    }


def set_test_override(
    db: Session,
    *,
    tenant_context: TenantContext,
    test_id: str,
    price: float | None = None,
    tat_hours: int | None = None,
    custom_name: str | None = None,
    custom_code: str | None = None,
    specimen_type: str | None = None,
    container_type: str | None = None,
    is_active: bool | None = None,
    parameters: list[dict[str, Any]] | None = None,
    actor_user_id: str | None = None,
) -> dict[str, Any]:
    """Create or update a tenant-local catalog override without modifying the system default."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id

    test = db.execute(
        select(Test).where(
            Test.id == test_id,
            or_(
                Test.tenant_id == tenant_id,
                Test.is_system_default == True,  # noqa: E712
            ),
        )
    ).scalar_one_or_none()

    if not test:
        raise NotFoundError(f"Test '{test_id}' not found.")

    if test.is_system_default:
        override = db.execute(
            select(TenantTestOverride).where(
                TenantTestOverride.tenant_id == tenant_id,
                TenantTestOverride.test_id == test_id,
            )
        ).scalar_one_or_none()

        if not override:
            override = TenantTestOverride(
                tenant_id=tenant_id,
                test_id=test_id,
                price=price if price is not None else test.base_price,
                tat_hours=tat_hours if tat_hours is not None else test.tat_hours,
                custom_name=custom_name.strip() if custom_name else None,
                custom_code=custom_code.strip() if custom_code else None,
                specimen_type=specimen_type.strip() if specimen_type else None,
                container_type=container_type.strip() if container_type else None,
                is_active=is_active if is_active is not None else True,
                sync_status="pending",
            )
            db.add(override)
        else:
            if price is not None:
                override.price = price
            if tat_hours is not None:
                override.tat_hours = tat_hours
            if custom_name is not None:
                override.custom_name = custom_name.strip() if custom_name else None
            if custom_code is not None:
                override.custom_code = custom_code.strip() if custom_code else None
            if specimen_type is not None:
                override.specimen_type = specimen_type.strip() if specimen_type else None
            if container_type is not None:
                override.container_type = container_type.strip() if container_type else None
            if is_active is not None:
                override.is_active = is_active
            override.sync_status = "pending"

        db.flush()

        # Queue durable sync event
        enqueue_sync_event(
            db,
            tenant_id=tenant_id,
            entity_type="tenant_test_override",
            entity_id=override.id,
            operation="upsert",
            payload={
                "test_id": test_id,
                "price": float(override.price) if override.price is not None else None,
                "tat_hours": override.tat_hours,
                "custom_name": override.custom_name,
                "custom_code": override.custom_code,
                "is_active": override.is_active,
            },
        )

        log_audit_event(
            db,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action_code="test_catalog.override_updated",
            entity_type="tenant_test_override",
            entity_id=override.id,
            after_json={"test_id": test_id, "price": float(override.price) if override.price is not None else None, "is_active": override.is_active},
        )
    else:
        # Tenant custom test: update directly
        if price is not None:
            test.base_price = price
        if tat_hours is not None:
            test.tat_hours = tat_hours
        if custom_name is not None:
            test.name = custom_name.strip()
            test.display_name = custom_name.strip()
        if custom_code is not None:
            test.code = custom_code.strip().upper()
        if specimen_type is not None:
            test.specimen_type = specimen_type.strip()
        if container_type is not None:
            test.container_type = container_type.strip()
        if is_active is not None:
            test.status = "active" if is_active else "inactive"

        db.flush()
        enqueue_sync_event(
            db,
            tenant_id=tenant_id,
            entity_type="test",
            entity_id=test.id,
            operation="update",
            payload={
                "code": test.code,
                "name": test.name,
                "price": float(test.base_price),
                "status": test.status,
            },
        )

    # Process parameter modifications / additions
    if parameters is not None:
        param_names = []
        for p_idx, p_data in enumerate(parameters, start=1):
            p_id = p_data.get("id")
            p_code = (p_data.get("code") or f"PARAM_{p_idx}").strip().upper()
            p_name = (p_data.get("name") or p_code).strip()
            p_unit = p_data.get("unit")
            p_res_type = p_data.get("result_type", "numeric")
            p_active = p_data.get("is_active", True)
            param_names.append(p_name)

            existing_p = None
            if p_id:
                existing_p = db.execute(
                    select(TestParameter).where(
                        TestParameter.id == p_id,
                        TestParameter.test_id == test_id,
                    )
                ).scalar_one_or_none()

            if existing_p:
                existing_p.code = p_code[:64]
                existing_p.name = p_name
                existing_p.unit = p_unit
                existing_p.result_type = p_res_type
                existing_p.is_active = p_active
                existing_p.sort_order = p_idx
                param_target = existing_p
            else:
                param_target = TestParameter(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    test_id=test_id,
                    code=p_code[:64],
                    name=p_name,
                    unit=p_unit,
                    result_type=p_res_type,
                    sort_order=p_idx,
                    is_active=p_active,
                )
                db.add(param_target)
                db.flush()

            # Process Reference Ranges
            ref_ranges = p_data.get("reference_ranges")
            if ref_ranges is not None:
                for r in ref_ranges:
                    r_id = r.get("id")
                    existing_r = None
                    if r_id:
                        existing_r = db.execute(
                            select(TestReferenceRange).where(
                                TestReferenceRange.id == r_id,
                                TestReferenceRange.parameter_id == param_target.id,
                            )
                        ).scalar_one_or_none()

                    if existing_r:
                        existing_r.sex = r.get("sex", "all")
                        existing_r.low_value = r.get("low_value")
                        existing_r.high_value = r.get("high_value")
                        existing_r.critical_low = r.get("critical_low")
                        existing_r.critical_high = r.get("critical_high")
                        existing_r.text_range = r.get("text_range")
                    else:
                        new_r = TestReferenceRange(
                            id=str(uuid.uuid4()),
                            test_id=test_id,
                            parameter_id=param_target.id,
                            tenant_id=tenant_id,
                            sex=r.get("sex", "all"),
                            age_unit="years",
                            priority=1,
                            low_value=r.get("low_value"),
                            high_value=r.get("high_value"),
                            critical_low=r.get("critical_low"),
                            critical_high=r.get("critical_high"),
                            text_range=r.get("text_range"),
                        )
                        db.add(new_r)

        if param_names:
            test.parameters_summary = ", ".join(param_names[:5]) + (f" (+{len(param_names)-5} more)" if len(param_names) > 5 else "")

    db.commit()
    return get_test_detail(db, tenant_context=tenant_context, test_id=test_id)


def add_parameter_to_test(
    db: Session,
    *,
    tenant_context: TenantContext,
    test_id: str,
    parameter_data: dict[str, Any],
) -> dict[str, Any]:
    """Add a new reportable parameter directly to a test."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id

    test = db.execute(
        select(Test).where(
            Test.id == test_id,
            or_(
                Test.tenant_id == tenant_id,
                Test.is_system_default == True,  # noqa: E712
            ),
        )
    ).scalar_one_or_none()
    if not test:
        raise NotFoundError(f"Test '{test_id}' not found.")

    p_code = (parameter_data.get("code") or "PARAM_NEW").strip().upper()
    p_name = (parameter_data.get("name") or p_code).strip()
    param = TestParameter(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        test_id=test_id,
        code=p_code[:64],
        name=p_name,
        unit=parameter_data.get("unit"),
        result_type=parameter_data.get("result_type", "numeric"),
        sort_order=parameter_data.get("sort_order", 99),
        is_active=parameter_data.get("is_active", True),
    )
    db.add(param)
    db.flush()

    for r in parameter_data.get("reference_ranges") or []:
        ref_range = TestReferenceRange(
            id=str(uuid.uuid4()),
            test_id=test_id,
            parameter_id=param.id,
            tenant_id=tenant_id,
            sex=r.get("sex", "all"),
            age_unit="years",
            priority=1,
            low_value=r.get("low_value"),
            high_value=r.get("high_value"),
            critical_low=r.get("critical_low"),
            critical_high=r.get("critical_high"),
            text_range=r.get("text_range"),
        )
        db.add(ref_range)

    # Update summary
    params = db.execute(select(TestParameter).where(TestParameter.test_id == test_id, TestParameter.is_active == True)).scalars().all()  # noqa: E712
    p_names = [p.name for p in params]
    test.parameters_summary = ", ".join(p_names[:5]) + (f" (+{len(p_names)-5} more)" if len(p_names) > 5 else "")
    db.commit()

    return {
        "id": param.id,
        "code": param.code,
        "name": param.name,
        "unit": param.unit,
        "result_type": param.result_type,
        "sort_order": param.sort_order,
        "is_active": param.is_active,
    }


def delete_test_parameter(
    db: Session,
    *,
    tenant_context: TenantContext,
    parameter_id: str,
) -> dict[str, Any]:
    """Delete or deactivate a reportable parameter from an investigation."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)

    param = db.execute(select(TestParameter).where(TestParameter.id == parameter_id)).scalar_one_or_none()
    if not param:
        raise NotFoundError(f"Parameter '{parameter_id}' not found.")

    test_id = param.test_id
    db.execute(select(TestReferenceRange).where(TestReferenceRange.parameter_id == parameter_id))
    # Delete reference ranges
    for rr in db.execute(select(TestReferenceRange).where(TestReferenceRange.parameter_id == parameter_id)).scalars().all():
        db.delete(rr)
    db.delete(param)
    db.flush()

    # Update test summary
    test = db.execute(select(Test).where(Test.id == test_id)).scalar_one_or_none()
    if test:
        remaining_params = db.execute(select(TestParameter).where(TestParameter.test_id == test_id)).scalars().all()
        p_names = [p.name for p in remaining_params]
        test.parameters_summary = ", ".join(p_names[:5]) + (f" (+{len(p_names)-5} more)" if len(p_names) > 5 else "")

    db.commit()
    return {"deleted": True, "parameter_id": parameter_id}


def reset_test_override(
    db: Session,
    *,
    tenant_context: TenantContext,
    test_id: str,
    actor_user_id: str | None = None,
) -> dict[str, Any]:
    """Delete a tenant-local override, reverting back to the system default catalog definition."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id

    override = db.execute(
        select(TenantTestOverride).where(
            TenantTestOverride.tenant_id == tenant_id,
            TenantTestOverride.test_id == test_id,
        )
    ).scalar_one_or_none()

    if override:
        ov_id = override.id
        db.delete(override)
        enqueue_sync_event(
            db,
            tenant_id=tenant_id,
            entity_type="tenant_test_override",
            entity_id=ov_id,
            operation="delete",
            payload={"test_id": test_id},
        )
        log_audit_event(
            db,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action_code="test_catalog.override_reset",
            entity_type="tenant_test_override",
            entity_id=ov_id,
            before_json={"test_id": test_id},
        )
        db.commit()

    return get_test_detail(db, tenant_context=tenant_context, test_id=test_id)


def bulk_update_tests(
    db: Session,
    *,
    tenant_context: TenantContext,
    test_ids: list[str],
    price_action: str | None = None,  # 'set_fixed', 'increase_pct', 'decrease_pct'
    price_value: float | None = None,
    tat_hours: int | None = None,
    is_active: bool | None = None,
    actor_user_id: str | None = None,
) -> dict[str, Any]:
    """Apply bulk pricing, TAT, and active/inactive updates across multiple investigations."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id

    updated_count = 0
    for tid in test_ids:
        test = db.execute(
            select(Test).where(
                Test.id == tid,
                or_(Test.tenant_id == tenant_id, Test.is_system_default == True),  # noqa: E712
            )
        ).scalar_one_or_none()
        if not test:
            continue

        override = db.execute(
            select(TenantTestOverride).where(
                TenantTestOverride.tenant_id == tenant_id,
                TenantTestOverride.test_id == tid,
            )
        ).scalar_one_or_none()

        curr_price = float(override.price if (override and override.price is not None) else (test.base_price or 0.0))
        target_price = None

        if price_action == "set_fixed" and price_value is not None:
            target_price = max(0.0, float(price_value))
        elif price_action == "increase_pct" and price_value is not None:
            target_price = max(0.0, round(curr_price * (1.0 + (float(price_value) / 100.0)), 2))
        elif price_action == "decrease_pct" and price_value is not None:
            target_price = max(0.0, round(curr_price * (1.0 - (float(price_value) / 100.0)), 2))

        if test.is_system_default:
            if not override:
                override = TenantTestOverride(
                    tenant_id=tenant_id,
                    test_id=tid,
                    price=target_price if target_price is not None else test.base_price,
                    tat_hours=tat_hours if tat_hours is not None else test.tat_hours,
                    is_active=is_active if is_active is not None else True,
                    sync_status="pending",
                )
                db.add(override)
            else:
                if target_price is not None:
                    override.price = target_price
                if tat_hours is not None:
                    override.tat_hours = tat_hours
                if is_active is not None:
                    override.is_active = is_active
                override.sync_status = "pending"
        else:
            if target_price is not None:
                test.base_price = target_price
            if tat_hours is not None:
                test.tat_hours = tat_hours
            if is_active is not None:
                test.status = "active" if is_active else "inactive"

        updated_count += 1

    db.commit()
    log_audit_event(
        db,
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        action_code="test_catalog.bulk_updated",
        entity_type="test_catalog",
        after_json={"updated_count": updated_count, "test_ids": test_ids},
    )
    return {"updated_count": updated_count, "affected_ids": test_ids}


def import_catalog_data(
    db: Session,
    *,
    tenant_context: TenantContext,
    tests_data: list[dict[str, Any]],
    mode: str = "upsert",  # 'insert_only', 'update_existing', 'upsert'
    dry_run: bool = False,
    actor_user_id: str | None = None,
) -> dict[str, Any]:
    """
    Import investigations and parameters from parsed spreadsheet.
    Supports Insert Only, Update Existing, and Upsert modes.
    Returns preview and validation statistics.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id

    # Index existing tenant tests and system default tests
    tenant_tests = {
        t.code.upper(): t
        for t in db.execute(select(Test).where(Test.tenant_id == tenant_id)).scalars().all()
    }
    system_tests = {
        t.code.upper(): t
        for t in db.execute(select(Test).where(Test.is_system_default == True)).scalars().all()  # noqa: E712
    }

    new_tests = []
    updated_tests = []
    skipped_tests = []
    invalid_rows = []
    price_changes = []

    for t_data in tests_data:
        raw_code = (t_data.get("code") or "").strip().upper()
        name = (t_data.get("name") or "").strip()
        price = float(t_data.get("price") or 0.0)

        if not name:
            invalid_rows.append({"row": t_data.get("row_index", 0), "code": raw_code, "reason": "Missing Investigation Name"})
            continue

        if not raw_code:
            raw_code = re.sub(r"[^A-Za-z0-9_]", "_", name.upper())[:32]

        matched_tenant = tenant_tests.get(raw_code)
        matched_system = system_tests.get(raw_code)

        if matched_tenant or matched_system:
            # Record already exists
            if mode == "insert_only":
                skipped_tests.append({"code": raw_code, "name": name, "reason": "Test already exists (insert_only mode)"})
                continue

            # Update Existing or Upsert
            base_test = matched_tenant or matched_system
            old_price = float(base_test.base_price)

            if matched_system:
                # System test: update/create tenant override
                if not dry_run:
                    override = db.execute(
                        select(TenantTestOverride).where(
                            TenantTestOverride.tenant_id == tenant_id,
                            TenantTestOverride.test_id == matched_system.id,
                        )
                    ).scalar_one_or_none()

                    if not override:
                        override = TenantTestOverride(
                            tenant_id=tenant_id,
                            test_id=matched_system.id,
                            price=price,
                            tat_hours=t_data.get("tat_hours", matched_system.tat_hours),
                            custom_name=name if name != matched_system.name else None,
                            is_active=True,
                            sync_status="pending",
                        )
                        db.add(override)
                    else:
                        override.price = price
                        override.tat_hours = t_data.get("tat_hours", override.tat_hours)
                        override.sync_status = "pending"
            else:
                # Tenant custom test: update directly
                if not dry_run:
                    matched_tenant.name = name
                    matched_tenant.display_name = name
                    matched_tenant.base_price = price
                    matched_tenant.tat_hours = t_data.get("tat_hours", matched_tenant.tat_hours)

            if old_price != price:
                price_changes.append({"code": raw_code, "name": name, "old_price": old_price, "new_price": price})

            updated_tests.append({"code": raw_code, "name": name, "price": price, "action": "override" if matched_system else "updated"})
        else:
            # Investigation does not exist
            if mode == "update_existing":
                skipped_tests.append({"code": raw_code, "name": name, "reason": "Investigation not found in catalog (update_existing mode)"})
                continue

            # Insert Only or Upsert
            if not dry_run:
                new_test = Test(
                    tenant_id=tenant_id,
                    code=raw_code,
                    name=name,
                    display_name=name,
                    specimen_type=t_data.get("sample_type", "Serum"),
                    container_type="Red (Plain / Gel)",
                    is_system_default=False,
                    base_price=price,
                    tat_hours=t_data.get("tat_hours", 4),
                    parameters_summary=t_data.get("parameters_summary"),
                    status="active",
                    version=1,
                )
                db.add(new_test)
                db.flush()

                # Add parameters
                for p in t_data.get("parameters", []):
                    param = TestParameter(
                        tenant_id=tenant_id,
                        test_id=new_test.id,
                        code=p["code"],
                        name=p["name"],
                        unit=p.get("unit"),
                        result_type=p.get("result_type", "numeric"),
                        sort_order=p.get("sort_order", 0),
                        is_active=True,
                    )
                    db.add(param)
                    db.flush()

                    for r in p.get("reference_ranges", []):
                        ref_range = TestReferenceRange(
                            test_id=new_test.id,
                            parameter_id=param.id,
                            tenant_id=tenant_id,
                            sex=r.get("sex", "all"),
                            low_value=r.get("low_value"),
                            high_value=r.get("high_value"),
                            text_range=r.get("text_range"),
                            needs_review=r.get("needs_review", False),
                        )
                        db.add(ref_range)

            new_tests.append({"code": raw_code, "name": name, "price": price, "action": "created"})

    if not dry_run:
        db.commit()
        enqueue_sync_event(
            db,
            tenant_id=tenant_id,
            entity_type="catalog_import",
            entity_id=str(uuid.uuid4()),
            operation="batch_import",
            payload={"mode": mode, "new_count": len(new_tests), "updated_count": len(updated_tests)},
        )
        log_audit_event(
            db,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action_code="test_catalog.imported",
            entity_type="test_catalog",
            after_json={"mode": mode, "new_count": len(new_tests), "updated_count": len(updated_tests)},
        )

    return {
        "mode": mode,
        "dry_run": dry_run,
        "total_rows": len(tests_data),
        "new_count": len(new_tests),
        "updated_count": len(updated_tests),
        "skipped_count": len(skipped_tests),
        "invalid_count": len(invalid_rows),
        "new_tests": new_tests[:50],
        "updated_tests": updated_tests[:50],
        "skipped_tests": skipped_tests[:50],
        "invalid_rows": invalid_rows,
        "price_changes": price_changes[:50],
    }


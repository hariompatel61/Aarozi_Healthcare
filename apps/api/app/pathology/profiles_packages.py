"""Pathology Profiles and Packages service: definition, cataloging, and recursive/flattened item expansion."""
from __future__ import annotations

from typing import Any
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.audit.service import log_audit_event
from app.errors import ConflictError, NotFoundError, ValidationError
from app.models.pathology import Package, PackageItem, Profile, ProfileItem, Test
from app.security.tenant_guard import TenantContext, verify_tenant_boundary


def create_profile(
    db: Session,
    *,
    tenant_context: TenantContext,
    code: str,
    name: str,
    display_name: str | None = None,
    department_id: str | None = None,
    description: str | None = None,
    test_ids: list[str] | None = None,
    actor_user_id: str | None = None,
) -> Profile:
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id

    clean_code = (code or "").strip().upper()
    if not clean_code:
        raise ValidationError("Profile code cannot be empty", field="code")
    clean_name = (name or "").strip()
    if not clean_name:
        raise ValidationError("Profile name cannot be empty", field="name")
    clean_display = (display_name or clean_name).strip()

    existing = db.execute(
        select(Profile).where(
            Profile.tenant_id == tenant_id,
            Profile.code == clean_code,
        )
    ).scalars().first()
    if existing:
        raise ConflictError(f"Profile with code '{clean_code}' already exists")

    profile = Profile(
        tenant_id=tenant_id,
        code=clean_code,
        name=clean_name,
        display_name=clean_display,
        department_id=department_id,
        description=description.strip() if description else None,
        status="active",
    )
    db.add(profile)
    db.flush()

    if test_ids:
        unique_test_ids = list(dict.fromkeys(test_ids))
        valid_tests = db.execute(
            select(Test).where(
                Test.tenant_id == tenant_id,
                Test.id.in_(unique_test_ids),
                Test.status == "active",
            )
        ).scalars().all()
        valid_map = {t.id: t for t in valid_tests}
        if len(valid_map) != len(unique_test_ids):
            missing = set(unique_test_ids) - set(valid_map.keys())
            raise NotFoundError(f"Tests not found or inactive in tenant: {missing}")

        for idx, t_id in enumerate(unique_test_ids):
            item = ProfileItem(
                profile_id=profile.id,
                test_id=t_id,
                sort_order=idx,
                is_mandatory=True,
            )
            db.add(item)

    log_audit_event(
        db,
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        action_code="profile.create",
        entity_type="profile",
        entity_id=profile.id,
        after_json={
            "code": profile.code,
            "name": profile.name,
            "test_count": len(test_ids or []),
        },
    )
    db.flush()
    return profile


def get_profile(db: Session, *, tenant_context: TenantContext, profile_id: str) -> Profile:
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    profile = db.execute(
        select(Profile)
        .options(joinedload(Profile.items).joinedload(ProfileItem.test))
        .where(
            Profile.id == profile_id,
            Profile.tenant_id == tenant_context.tenant_id,
        )
    ).unique().scalars().first()
    if not profile:
        raise NotFoundError(f"Profile '{profile_id}' not found")
    return profile


def list_profiles(
    db: Session,
    *,
    tenant_context: TenantContext,
    status: str | None = "active",
    search: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[Profile]:
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id

    limit = min(max(1, limit), 50)
    offset = max(0, offset)

    stmt = select(Profile).where(Profile.tenant_id == tenant_id)
    if status:
        stmt = stmt.where(Profile.status == status)
    if search:
        search_term = f"%{search.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Profile.code).like(search_term),
                func.lower(Profile.name).like(search_term),
                func.lower(Profile.display_name).like(search_term),
            )
        )

    stmt = stmt.order_by(Profile.name.asc()).limit(limit).offset(offset)
    return list(db.execute(stmt).scalars().all())


def create_package(
    db: Session,
    *,
    tenant_context: TenantContext,
    code: str,
    name: str,
    display_name: str | None = None,
    description: str | None = None,
    items: list[dict[str, Any]] | None = None,
    actor_user_id: str | None = None,
) -> Package:
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id

    clean_code = (code or "").strip().upper()
    if not clean_code:
        raise ValidationError("Package code cannot be empty", field="code")
    clean_name = (name or "").strip()
    if not clean_name:
        raise ValidationError("Package name cannot be empty", field="name")
    clean_display = (display_name or clean_name).strip()

    existing = db.execute(
        select(Package).where(
            Package.tenant_id == tenant_id,
            Package.code == clean_code,
        )
    ).scalars().first()
    if existing:
        raise ConflictError(f"Package with code '{clean_code}' already exists")

    package = Package(
        tenant_id=tenant_id,
        code=clean_code,
        name=clean_name,
        display_name=clean_display,
        description=description.strip() if description else None,
        status="active",
    )
    db.add(package)
    db.flush()

    if items:
        for idx, item_def in enumerate(items):
            test_id = item_def.get("test_id")
            profile_id = item_def.get("profile_id")
            if not test_id and not profile_id:
                raise ValidationError("Package item must specify test_id or profile_id")
            if test_id and profile_id:
                raise ValidationError("Package item cannot specify both test_id and profile_id")

            if test_id:
                test = db.execute(
                    select(Test).where(
                        Test.id == test_id,
                        Test.tenant_id == tenant_id,
                        Test.status == "active",
                    )
                ).scalars().first()
                if not test:
                    raise NotFoundError(f"Test '{test_id}' not found or inactive in tenant")
            if profile_id:
                prof = db.execute(
                    select(Profile).where(
                        Profile.id == profile_id,
                        Profile.tenant_id == tenant_id,
                        Profile.status == "active",
                    )
                ).scalars().first()
                if not prof:
                    raise NotFoundError(f"Profile '{profile_id}' not found or inactive in tenant")

            pkg_item = PackageItem(
                package_id=package.id,
                test_id=test_id,
                profile_id=profile_id,
                sort_order=item_def.get("sort_order", idx),
            )
            db.add(pkg_item)

    log_audit_event(
        db,
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        action_code="package.create",
        entity_type="package",
        entity_id=package.id,
        after_json={
            "code": package.code,
            "name": package.name,
            "item_count": len(items or []),
        },
    )
    db.flush()
    return package


def get_package(db: Session, *, tenant_context: TenantContext, package_id: str) -> Package:
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    package = db.execute(
        select(Package)
        .options(
            joinedload(Package.items).joinedload(PackageItem.test),
            joinedload(Package.items).joinedload(PackageItem.profile).joinedload(Profile.items).joinedload(ProfileItem.test),
        )
        .where(
            Package.id == package_id,
            Package.tenant_id == tenant_context.tenant_id,
        )
    ).unique().scalars().first()
    if not package:
        raise NotFoundError(f"Package '{package_id}' not found")
    return package


def list_packages(
    db: Session,
    *,
    tenant_context: TenantContext,
    status: str | None = "active",
    search: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[Package]:
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id

    limit = min(max(1, limit), 50)
    offset = max(0, offset)

    stmt = select(Package).where(Package.tenant_id == tenant_id)
    if status:
        stmt = stmt.where(Package.status == status)
    if search:
        search_term = f"%{search.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Package.code).like(search_term),
                func.lower(Package.name).like(search_term),
                func.lower(Package.display_name).like(search_term),
            )
        )

    stmt = stmt.order_by(Package.name.asc()).limit(limit).offset(offset)
    return list(db.execute(stmt).scalars().all())


def expand_ordered_items(
    db: Session,
    *,
    tenant_context: TenantContext,
    items: list[dict[str, str]],
) -> list[dict[str, Any]]:
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id

    expanded_tests: dict[str, dict[str, Any]] = {}

    for entry in items:
        item_type = entry.get("type")
        item_id = entry.get("id")
        if not item_type or not item_id:
            raise ValidationError("Each item must specify type and id")

        if item_type == "test":
            test = db.execute(
                select(Test).where(
                    Test.id == item_id,
                    Test.tenant_id == tenant_id,
                    Test.status == "active",
                )
            ).scalars().first()
            if not test:
                raise NotFoundError(f"Test '{item_id}' not found or inactive")
            if test.id not in expanded_tests:
                expanded_tests[test.id] = {
                    "test_id": test.id,
                    "code": test.code,
                    "name": test.name,
                    "specimen_type": test.specimen_type,
                    "container_type": test.container_type,
                    "unit": test.unit,
                    "sources": [{"type": "test", "id": test.id, "name": test.name}],
                }
            else:
                expanded_tests[test.id]["sources"].append({"type": "test", "id": test.id, "name": test.name})

        elif item_type == "profile":
            profile = get_profile(db, tenant_context=tenant_context, profile_id=item_id)
            if profile.status != "active":
                raise ValidationError(f"Profile '{profile.name}' is inactive")
            for p_item in profile.items:
                test = p_item.test
                if test and test.status == "active":
                    source_meta = {"type": "profile", "id": profile.id, "name": profile.name}
                    if test.id not in expanded_tests:
                        expanded_tests[test.id] = {
                            "test_id": test.id,
                            "code": test.code,
                            "name": test.name,
                            "specimen_type": test.specimen_type,
                            "container_type": test.container_type,
                            "unit": test.unit,
                            "sources": [source_meta],
                        }
                    else:
                        expanded_tests[test.id]["sources"].append(source_meta)

        elif item_type == "package":
            package = get_package(db, tenant_context=tenant_context, package_id=item_id)
            if package.status != "active":
                raise ValidationError(f"Package '{package.name}' is inactive")
            for pkg_item in package.items:
                if pkg_item.test_id and pkg_item.test and pkg_item.test.status == "active":
                    test = pkg_item.test
                    source_meta = {"type": "package", "id": package.id, "name": package.name}
                    if test.id not in expanded_tests:
                        expanded_tests[test.id] = {
                            "test_id": test.id,
                            "code": test.code,
                            "name": test.name,
                            "specimen_type": test.specimen_type,
                            "container_type": test.container_type,
                            "unit": test.unit,
                            "sources": [source_meta],
                        }
                    else:
                        expanded_tests[test.id]["sources"].append(source_meta)
                elif pkg_item.profile_id and pkg_item.profile and pkg_item.profile.status == "active":
                    prof = pkg_item.profile
                    for p_item in prof.items:
                        test = p_item.test
                        if test and test.status == "active":
                            source_meta = {
                                "type": "package",
                                "id": package.id,
                                "name": package.name,
                                "via_profile": prof.name,
                            }
                            if test.id not in expanded_tests:
                                expanded_tests[test.id] = {
                                    "test_id": test.id,
                                    "code": test.code,
                                    "name": test.name,
                                    "specimen_type": test.specimen_type,
                                    "container_type": test.container_type,
                                    "unit": test.unit,
                                    "sources": [source_meta],
                                }
                            else:
                                expanded_tests[test.id]["sources"].append(source_meta)
        else:
            raise ValidationError(f"Invalid item type: '{item_type}'. Must be test, profile, or package.")

    return list(expanded_tests.values())

"""Blood Bank TTI & Component Testing Service (P07-05)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.errors import NotFoundError, ValidationError, ForbiddenError, ConflictError
from app.models.blood_bank import BloodUnit, BloodUnitTest
from app.models.identity import Permission, RolePermission, UserRole
from app.security.tenant_guard import TenantContext

REQUIRED_TTI_TESTS = ["HIV", "HBSAG", "HCV", "VDRL", "MALARIA"]


def _check_testing_permission(
    db: Session,
    *,
    tenant_context: TenantContext,
    permission_code: str = "blood.unit.receive",
    actor_user_id: str | None = None,
) -> None:
    if tenant_context.is_superuser:
        return

    effective_user_id = actor_user_id or tenant_context.user_id
    if not effective_user_id:
        raise ForbiddenError("Authenticated actor required for blood testing operations")

    has_perm = (
        db.query(RolePermission)
        .join(UserRole, UserRole.role_id == RolePermission.role_id)
        .join(Permission, Permission.id == RolePermission.permission_id)
        .filter(
            UserRole.user_id == effective_user_id,
            Permission.code.in_([permission_code, "blood.unit.receive", "blood.unit.verify"]),
            RolePermission.allow.is_(True),
        )
        .first()
    )
    if not has_perm:
        raise ForbiddenError(f"User lacks required permission '{permission_code}'")


def record_blood_unit_tests(
    db: Session,
    *,
    tenant_context: TenantContext,
    blood_unit_id: str,
    tests_input: list[dict[str, Any]],
) -> list[BloodUnitTest]:
    _check_testing_permission(db, tenant_context=tenant_context)

    unit = (
        db.query(BloodUnit)
        .filter(
            BloodUnit.id == blood_unit_id,
            BloodUnit.tenant_id == tenant_context.tenant_id,
        )
        .first()
    )
    if not unit:
        raise NotFoundError("Blood unit not found")

    created_tests: list[BloodUnitTest] = []
    for item in tests_input:
        test_code = item.get("test_code")
        if not test_code:
            raise ValidationError("test_code is required for blood unit test")

        existing = (
            db.query(BloodUnitTest)
            .filter(
                BloodUnitTest.blood_unit_id == unit.id,
                BloodUnitTest.test_code == test_code,
            )
            .first()
        )
        if existing:
            raise ConflictError(f"Test '{test_code}' already exists for blood unit {unit.unit_no}")

        blood_test = BloodUnitTest(
            tenant_id=tenant_context.tenant_id,
            blood_unit_id=unit.id,
            test_code=test_code,
            result=item.get("result"),
            status="pending",
        )
        db.add(blood_test)
        created_tests.append(blood_test)

    # Update unit status to testing if collected
    if unit.status == "collected":
        unit.status = "testing"

    db.commit()
    for t in created_tests:
        db.refresh(t)
    return created_tests


def verify_blood_unit_test(
    db: Session,
    *,
    tenant_context: TenantContext,
    test_id: str,
    result: str,
    actor_user_id: str | None = None,
) -> BloodUnitTest:
    _check_testing_permission(db, tenant_context=tenant_context, permission_code="blood.unit.receive")

    blood_test = (
        db.query(BloodUnitTest)
        .filter(
            BloodUnitTest.id == test_id,
            BloodUnitTest.tenant_id == tenant_context.tenant_id,
        )
        .first()
    )
    if not blood_test:
        raise NotFoundError("Blood unit test record not found")

    blood_test.result = result
    blood_test.status = "verified"
    blood_test.verified_by = actor_user_id or tenant_context.user_id
    blood_test.verified_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(blood_test)
    return blood_test


def list_blood_unit_tests(
    db: Session,
    *,
    tenant_context: TenantContext,
    blood_unit_id: str,
) -> list[BloodUnitTest]:
    return (
        db.query(BloodUnitTest)
        .filter(
            BloodUnitTest.tenant_id == tenant_context.tenant_id,
            BloodUnitTest.blood_unit_id == blood_unit_id,
        )
        .all()
    )


def check_unit_testing_clearance(
    db: Session,
    *,
    tenant_context: TenantContext,
    blood_unit_id: str,
) -> dict[str, Any]:
    tests = list_blood_unit_tests(db, tenant_context=tenant_context, blood_unit_id=blood_unit_id)
    test_map = {t.test_code: t for t in tests}

    missing = [code for code in REQUIRED_TTI_TESTS if code not in test_map]
    pending = [code for code, t in test_map.items() if t.status != "verified"]
    reactive = [
        code for code, t in test_map.items()
        if t.status == "verified" and t.result and t.result.lower() in ["positive", "reactive"]
    ]

    cleared = len(missing) == 0 and len(pending) == 0 and len(reactive) == 0

    return {
        "cleared": cleared,
        "missing": missing,
        "pending": pending,
        "reactive": reactive,
        "tests": tests,
    }

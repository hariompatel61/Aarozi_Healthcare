"""Authorization engine: Server-side permission resolver and policy checks."""

from __future__ import annotations

from typing import Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.identity import User, UserRole, Role, RolePermission, Permission
from app.rbac.scope import user_has_branch_access, user_has_department_access
from app.errors import ForbiddenError


def resolve_user_permissions(db: Session, user: User) -> set[str]:
    """Resolve all granted permission codes for a user within their tenant."""
    if not user.is_active:
        return set()

    if user.is_superuser:
        # Superuser has all permissions
        stmt = select(Permission.code)
        return set(db.scalars(stmt).all())

    # Fetch active roles assigned to the user within user's tenant
    stmt = (
        select(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(Role, Role.id == RolePermission.role_id)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(
            UserRole.user_id == user.id,
            Role.tenant_id == user.tenant_id,
            Role.status == "active",
            RolePermission.allow.is_(True),
        )
    )
    return set(db.scalars(stmt).all())


def authorize_action(
    db: Session,
    user: User,
    permission_code: str,
    *,
    branch_id: str | None = None,
    department_id: str | None = None,
) -> bool:
    """Check if user has permission and is authorized for optional branch/department scope."""
    if not user.is_active:
        return False

    if user.is_superuser:
        return True

    # Check permission grant
    granted = resolve_user_permissions(db, user)
    if permission_code not in granted:
        return False

    # Check branch scope if branch_id is specified
    if branch_id or department_id:
        user_roles = db.scalars(
            select(UserRole)
            .join(Role, Role.id == UserRole.role_id)
            .join(RolePermission, RolePermission.role_id == Role.id)
            .join(Permission, Permission.id == RolePermission.permission_id)
            .where(
                UserRole.user_id == user.id,
                Role.tenant_id == user.tenant_id,
                Role.status == "active",
                Permission.code == permission_code,
                RolePermission.allow.is_(True),
            )
        ).all()

        if branch_id and not user_has_branch_access(user_roles, branch_id):
            return False

        if department_id and not user_has_department_access(user_roles, department_id):
            return False

    return True


def enforce_permission(
    db: Session,
    user: User,
    permission_code: str,
    *,
    branch_id: str | None = None,
    department_id: str | None = None,
) -> None:
    """Enforces authorization, raising ForbiddenError if permission check fails."""
    if not authorize_action(db, user, permission_code, branch_id=branch_id, department_id=department_id):
        raise ForbiddenError(f"Permission denied: {permission_code}")

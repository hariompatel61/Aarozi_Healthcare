"""User role scope management and verification (branch & department scoping)."""

from __future__ import annotations

from typing import Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.identity import User, Role, UserRole
from app.models.core import Branch, Department
from app.errors import NotFoundError, ValidationError


def assign_role_to_user(
    db: Session,
    *,
    user_id: str,
    role_id: str,
    branch_ids: Sequence[str] | None = None,
    department_ids: Sequence[str] | None = None,
) -> UserRole:
    user = db.get(User, user_id)
    if not user:
        raise NotFoundError("User not found")

    role = db.get(Role, role_id)
    if not role:
        raise NotFoundError("Role not found")

    if role.tenant_id != user.tenant_id:
        raise ValidationError("Cannot assign role from a different tenant")

    # Validate branch scopes belong to tenant if provided
    if branch_ids:
        valid_branch_count = db.query(Branch).filter(
            Branch.tenant_id == user.tenant_id,
            Branch.id.in_(branch_ids),
        ).count()
        if valid_branch_count != len(branch_ids):
            raise ValidationError("One or more branch IDs do not belong to user tenant")

    # Validate department scopes belong to tenant if provided
    if department_ids:
        valid_dept_count = db.query(Department).filter(
            Department.tenant_id == user.tenant_id,
            Department.id.in_(department_ids),
        ).count()
        if valid_dept_count != len(department_ids):
            raise ValidationError("One or more department IDs do not belong to user tenant")

    existing = db.execute(
        select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id)
    ).scalar_one_or_none()

    if existing:
        existing.branch_scope_json = list(branch_ids) if branch_ids is not None else None
        existing.department_scope_json = list(department_ids) if department_ids is not None else None
        user_role = existing
    else:
        user_role = UserRole(
            user_id=user_id,
            role_id=role_id,
            branch_scope_json=list(branch_ids) if branch_ids is not None else None,
            department_scope_json=list(department_ids) if department_ids is not None else None,
        )
        db.add(user_role)

    db.commit()
    db.refresh(user_role)
    return user_role


def user_has_branch_access(user_roles: Sequence[UserRole], branch_id: str) -> bool:
    """Returns True if any role has global scope (None) or explicitly contains branch_id."""
    for ur in user_roles:
        if ur.branch_scope_json is None:
            return True
        if branch_id in ur.branch_scope_json:
            return True
    return False


def user_has_department_access(user_roles: Sequence[UserRole], department_id: str) -> bool:
    """Returns True if any role has global scope (None) or explicitly contains department_id."""
    for ur in user_roles:
        if ur.department_scope_json is None:
            return True
        if department_id in ur.department_scope_json:
            return True
    return False

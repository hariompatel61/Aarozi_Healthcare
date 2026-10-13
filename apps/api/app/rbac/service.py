"""Role management service: multi-tenant role CRUD and permission assignment."""

from __future__ import annotations

from typing import Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.identity import Role, RolePermission, Permission
from app.errors import ConflictError, NotFoundError, ValidationError


def create_role(
    db: Session,
    *,
    tenant_id: str,
    name: str,
    description: str | None = None,
    is_system: bool = False,
    permission_ids: Sequence[str] | None = None,
) -> Role:
    existing = db.execute(
        select(Role).where(Role.tenant_id == tenant_id, Role.name == name)
    ).scalar_one_or_none()
    if existing:
        raise ConflictError(f"Role '{name}' already exists for this tenant")

    role = Role(
        tenant_id=tenant_id,
        name=name,
        description=description,
        is_system=is_system,
        status="active",
    )
    db.add(role)
    db.flush()

    if permission_ids:
        assign_permissions_to_role(db, role_id=role.id, permission_ids=permission_ids)

    db.commit()
    db.refresh(role)
    return role


def assign_permissions_to_role(
    db: Session,
    *,
    role_id: str,
    permission_ids: Sequence[str],
) -> None:
    role = db.get(Role, role_id)
    if not role:
        raise NotFoundError("Role not found")

    # Clear existing role permissions
    for rp in list(role.role_permissions):
        db.delete(rp)
    db.flush()

    # Verify and add new permissions
    for pid in permission_ids:
        perm = db.get(Permission, pid)
        if perm:
            db.add(RolePermission(role_id=role.id, permission_id=perm.id, allow=True))
    db.flush()


def get_roles_by_tenant(
    db: Session,
    *,
    tenant_id: str,
    limit: int = 50,
    offset: int = 0,
) -> list[Role]:
    limit = min(limit, 100)  # enforce performance bounds
    stmt = (
        select(Role)
        .where(Role.tenant_id == tenant_id)
        .order_by(Role.name)
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(stmt).all())


def delete_role(db: Session, *, tenant_id: str, role_id: str) -> None:
    role = db.execute(
        select(Role).where(Role.tenant_id == tenant_id, Role.id == role_id)
    ).scalar_one_or_none()
    if not role:
        raise NotFoundError("Role not found")
    if role.is_system:
        raise ValidationError("Cannot delete a system role")
    db.delete(role)
    db.commit()

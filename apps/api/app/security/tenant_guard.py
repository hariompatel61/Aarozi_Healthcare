"""Multi-tenant isolation guards and context enforcement."""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any
from sqlalchemy import Select
from sqlalchemy.orm import Session

from app.errors import ForbiddenError, NotFoundError

# Thread-safe / async-safe current tenant context
_tenant_context_var: ContextVar[TenantContext | None] = ContextVar("tenant_context", default=None)


@dataclass(frozen=True)
class TenantContext:
    tenant_id: str
    user_id: str | None = None
    branch_id: str | None = None
    is_superuser: bool = False


def set_tenant_context(context: TenantContext) -> None:
    _tenant_context_var.set(context)


def get_tenant_context() -> TenantContext | None:
    return _tenant_context_var.get()


def clear_tenant_context() -> None:
    _tenant_context_var.set(None)


def verify_tenant_boundary(resource_tenant_id: str, context: TenantContext | None = None) -> None:
    """Ensures a resource belongs to the current authenticated tenant context.

    Raises ForbiddenError on cross-tenant violation.
    """
    ctx = context or get_tenant_context()
    if ctx is None:
        raise ForbiddenError("Tenant context is required")

    if ctx.is_superuser:
        return

    if resource_tenant_id != ctx.tenant_id:
        raise ForbiddenError("Cross-tenant access forbidden")


def apply_tenant_filter(stmt: Select[Any], model: Any, context: TenantContext | None = None) -> Select[Any]:
    """Applies tenant_id filter to a SQLAlchemy Select statement."""
    ctx = context or get_tenant_context()
    if ctx is None:
        raise ForbiddenError("Tenant context is required")

    if ctx.is_superuser:
        return stmt

    if hasattr(model, "tenant_id"):
        return stmt.where(model.tenant_id == ctx.tenant_id)

    return stmt

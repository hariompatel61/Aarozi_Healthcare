"""Multi-tenant isolation guards and context enforcement."""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any
from fastapi import Header
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


def get_tenant_context(authorization: str | None = Header(None)) -> TenantContext | None:
    ctx = _tenant_context_var.get()
    if ctx is not None:
        return ctx

    # Late extraction if header is present
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            from datetime import datetime
            from sqlalchemy import select
            from app.db import get_sync_session_factory
            from app.models.identity import SessionRecord

            token = parts[1]
            factory = get_sync_session_factory()
            with factory() as session:
                rec = session.scalar(
                    select(SessionRecord).where(
                        (SessionRecord.session_token == token)
                        & (SessionRecord.revoked_at.is_(None))
                        & (SessionRecord.expires_at > datetime.utcnow())
                    )
                )
                if rec and rec.user and rec.user.is_active:
                    ctx = TenantContext(
                        tenant_id=rec.tenant_id,
                        user_id=rec.user_id,
                        is_superuser=rec.user.is_superuser,
                    )
                    set_tenant_context(ctx)
                    return ctx

    if ctx is None:
        from app.settings import get_settings
        settings = get_settings()
        if not settings.is_production:
            from app.db import get_sync_session_factory
            from app.models.core import Tenant
            from sqlalchemy import select
            tenant_uuid = "AAROZI_HQ"
            try:
                factory = get_sync_session_factory()
                with factory() as session:
                    t = session.scalar(select(Tenant).where((Tenant.code == "AAROZI_HQ") | (Tenant.id == "AAROZI_HQ")))
                    if t:
                        tenant_uuid = t.id
            except Exception:
                pass
            ctx = TenantContext(tenant_id=tenant_uuid, is_superuser=True)
            set_tenant_context(ctx)
            return ctx

    return ctx


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

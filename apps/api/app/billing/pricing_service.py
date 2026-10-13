"""Billing and Pricing Engine service: price lists, branch rates, effective dates, and resolution."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.audit.service import log_audit_event
from app.errors import ConflictError, NotFoundError, ValidationError
from app.models.billing import PriceList, PriceListItem
from app.security.tenant_guard import TenantContext, verify_tenant_boundary


class PriceListNotFoundError(NotFoundError):
    """Raised when a price list is not found."""
    pass


class PriceListItemNotFoundError(NotFoundError):
    """Raised when a price list item is not found."""
    pass
def create_price_list(
    db: Session,
    *,
    tenant_context: TenantContext,
    code: str,
    name: str,
    branch_id: str | None = None,
    description: str | None = None,
    currency: str = "USD",
    is_default: bool = False,
    status: str = "active",
    effective_from: datetime | None = None,
    effective_to: datetime | None = None,
    items: list[dict[str, Any]] | None = None,
    actor_user_id: str | None = None,
) -> PriceList:
    """Create a new price list with optional initial line items."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id

    clean_code = (code or "").strip().upper()
    if not clean_code:
        raise ValidationError("Price list code cannot be empty", field="code")
    clean_name = (name or "").strip()
    if not clean_name:
        raise ValidationError("Price list name cannot be empty", field="name")

    if effective_from is None:
        effective_from = datetime.now(timezone.utc)
    if effective_to is not None and effective_to <= effective_from:
        raise ValidationError("effective_to must be after effective_from", field="effective_to")

    existing = db.execute(
        select(PriceList).where(
            PriceList.tenant_id == tenant_id,
            PriceList.code == clean_code,
        )
    ).scalars().first()
    if existing:
        raise ConflictError(f"Price list with code '{clean_code}' already exists")

    if is_default:
        db.query(PriceList).filter(
            PriceList.tenant_id == tenant_id,
            PriceList.branch_id == branch_id,
            PriceList.is_default.is_(True),
        ).update({"is_default": False})

    price_list = PriceList(
        tenant_id=tenant_id,
        branch_id=branch_id,
        code=clean_code,
        name=clean_name,
        description=description.strip() if description else None,
        currency=(currency or "USD").strip().upper(),
        is_default=is_default,
        status=status,
        effective_from=effective_from,
        effective_to=effective_to,
    )
    db.add(price_list)
    db.flush()

    if items:
        for item_data in items:
            add_item_to_price_list(
                db,
                tenant_context=tenant_context,
                price_list_id=price_list.id,
                item_type=item_data["item_type"],
                item_id=item_data["item_id"],
                rate=item_data["rate"],
                min_rate=item_data.get("min_rate"),
                max_discount_pct=item_data.get("max_discount_pct", 0.0),
                is_active=item_data.get("is_active", True),
            )

    log_audit_event(
        db,
        tenant_id=tenant_id,
        actor_user_id=actor_user_id or tenant_context.user_id,
        action_code="price_list.created",
        entity_type="price_list",
        entity_id=price_list.id,
        after_json={
            "code": price_list.code,
            "name": price_list.name,
            "branch_id": price_list.branch_id,
            "is_default": price_list.is_default,
        },
    )

    db.commit()
    db.refresh(price_list)
    return price_list


def get_price_list(
    db: Session,
    *,
    tenant_context: TenantContext,
    price_list_id: str,
) -> PriceList:
    """Fetch price list by ID ensuring tenant isolation."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    price_list = db.execute(
        select(PriceList)
        .options(joinedload(PriceList.items))
        .where(
            PriceList.tenant_id == tenant_context.tenant_id,
            PriceList.id == price_list_id,
        )
    ).scalars().unique().first()

    if not price_list:
        raise PriceListNotFoundError(f"Price list '{price_list_id}' not found")
    return price_list


def list_price_lists(
    db: Session,
    *,
    tenant_context: TenantContext,
    branch_id: str | None = None,
    status: str | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[PriceList], int]:
    """List price lists with tenant scoping and bounded pagination."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id

    clamped_limit = max(1, min(limit, 100))
    clamped_offset = max(0, offset)

    query = select(PriceList).where(PriceList.tenant_id == tenant_id)

    if branch_id is not None:
        query = query.where(PriceList.branch_id == branch_id)
    if status:
        query = query.where(PriceList.status == status)
    if search:
        search_filter = f"%{search.strip().lower()}%"
        query = query.where(
            or_(
                func.lower(PriceList.code).like(search_filter),
                func.lower(PriceList.name).like(search_filter),
            )
        )

    count_stmt = select(func.count()).select_from(query.subquery())
    total = db.scalar(count_stmt) or 0

    results = db.execute(
        query.order_by(PriceList.created_at.desc())
        .offset(clamped_offset)
        .limit(clamped_limit)
    ).scalars().all()

    return list(results), total


def add_item_to_price_list(
    db: Session,
    *,
    tenant_context: TenantContext,
    price_list_id: str,
    item_type: str,
    item_id: str,
    rate: float,
    min_rate: float | None = None,
    max_discount_pct: float = 0.0,
    is_active: bool = True,
    actor_user_id: str | None = None,
) -> PriceListItem:
    """Add or update an item within a price list."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id

    plist = db.execute(
        select(PriceList).where(
            PriceList.tenant_id == tenant_id,
            PriceList.id == price_list_id,
        )
    ).scalars().first()
    if not plist:
        raise PriceListNotFoundError(f"Price list '{price_list_id}' not found")

    clean_type = item_type.strip().lower()
    if clean_type not in ("test", "profile", "package"):
        raise ValidationError(f"Invalid item_type '{item_type}'. Must be test, profile, or package", field="item_type")

    if rate < 0:
        raise ValidationError("Rate cannot be negative", field="rate")
    if min_rate is not None and min_rate < 0:
        raise ValidationError("min_rate cannot be negative", field="min_rate")
    if max_discount_pct < 0 or max_discount_pct > 100:
        raise ValidationError("max_discount_pct must be between 0 and 100", field="max_discount_pct")

    existing = db.execute(
        select(PriceListItem).where(
            PriceListItem.tenant_id == tenant_id,
            PriceListItem.price_list_id == price_list_id,
            PriceListItem.item_type == clean_type,
            PriceListItem.item_id == item_id,
        )
    ).scalars().first()

    if existing:
        existing.rate = rate
        existing.min_rate = min_rate
        existing.max_discount_pct = max_discount_pct
        existing.is_active = is_active
        db.flush()
        return existing
    item = PriceListItem(
        tenant_id=tenant_id,
        price_list_id=price_list_id,
        item_type=clean_type,
        item_id=item_id,
        rate=rate,
        min_rate=min_rate,
        max_discount_pct=max_discount_pct,
        is_active=is_active,
    )
    db.add(item)
    db.flush()
    return item



def resolve_pricing_rate(
    db: Session,
    *,
    tenant_context: TenantContext,
    item_type: str,
    item_id: str,
    branch_id: str | None = None,
    as_of: datetime | None = None,
) -> dict[str, Any]:
    """
    Resolve item pricing rate according to the canonical hierarchy:
    1. Active branch-specific price list effective as of date
    2. Active tenant default price list effective as of date
    3. Active tenant standard price list effective as of date
    4. Base fallback rate 0.0
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = tenant_context.tenant_id
    effective_time = as_of or datetime.now(timezone.utc)
    clean_type = item_type.strip().lower()

    # Step 1: Check branch price list
    target_branch_id = branch_id or tenant_context.branch_id
    if target_branch_id:
        branch_rate_item = db.execute(
            select(PriceListItem)
            .join(PriceList, PriceListItem.price_list_id == PriceList.id)
            .where(
                PriceListItem.tenant_id == tenant_id,
                PriceListItem.item_type == clean_type,
                PriceListItem.item_id == item_id,
                PriceListItem.is_active.is_(True),
                PriceList.branch_id == target_branch_id,
                PriceList.status == "active",
                PriceList.effective_from <= effective_time,
                or_(
                    PriceList.effective_to.is_(None),
                    PriceList.effective_to >= effective_time,
                ),
            )
            .order_by(PriceList.created_at.desc())
        ).scalars().first()

        if branch_rate_item:
            return {
                "source": "branch_rate",
                "price_list_id": branch_rate_item.price_list_id,
                "item_type": clean_type,
                "item_id": item_id,
                "rate": float(branch_rate_item.rate),
                "min_rate": float(branch_rate_item.min_rate) if branch_rate_item.min_rate is not None else None,
                "max_discount_pct": float(branch_rate_item.max_discount_pct),
            }

    # Step 2: Check tenant default price list
    tenant_rate_item = db.execute(
        select(PriceListItem)
        .join(PriceList, PriceListItem.price_list_id == PriceList.id)
        .where(
            PriceListItem.tenant_id == tenant_id,
            PriceListItem.item_type == clean_type,
            PriceListItem.item_id == item_id,
            PriceListItem.is_active.is_(True),
            PriceList.is_default.is_(True),
            PriceList.status == "active",
            PriceList.effective_from <= effective_time,
            or_(
                PriceList.effective_to.is_(None),
                PriceList.effective_to >= effective_time,
            ),
        )
        .order_by(PriceList.created_at.desc())
    ).scalars().first()

    if tenant_rate_item:
        return {
            "source": "tenant_default",
            "price_list_id": tenant_rate_item.price_list_id,
            "item_type": clean_type,
            "item_id": item_id,
            "rate": float(tenant_rate_item.rate),
            "min_rate": float(tenant_rate_item.min_rate) if tenant_rate_item.min_rate is not None else None,
            "max_discount_pct": float(tenant_rate_item.max_discount_pct),
        }

    # Step 3: Check any active tenant-wide price list if no default was explicitly marked
    any_tenant_rate = db.execute(
        select(PriceListItem)
        .join(PriceList, PriceListItem.price_list_id == PriceList.id)
        .where(
            PriceListItem.tenant_id == tenant_id,
            PriceListItem.item_type == clean_type,
            PriceListItem.item_id == item_id,
            PriceListItem.is_active.is_(True),
            PriceList.branch_id.is_(None),
            PriceList.status == "active",
            PriceList.effective_from <= effective_time,
            or_(
                PriceList.effective_to.is_(None),
                PriceList.effective_to >= effective_time,
            ),
        )
        .order_by(PriceList.created_at.desc())
    ).scalars().first()

    if any_tenant_rate:
        return {
            "source": "tenant_standard",
            "price_list_id": any_tenant_rate.price_list_id,
            "item_type": clean_type,
            "item_id": item_id,
            "rate": float(any_tenant_rate.rate),
            "min_rate": float(any_tenant_rate.min_rate) if any_tenant_rate.min_rate is not None else None,
            "max_discount_pct": float(any_tenant_rate.max_discount_pct),
        }

    # Fallback default
    return {
        "source": "base_fallback",
        "price_list_id": None,
        "item_type": clean_type,
        "item_id": item_id,
        "rate": 0.0,
        "min_rate": None,
        "max_discount_pct": 0.0,
    }



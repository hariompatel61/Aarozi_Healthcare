"""Blood Bank Inventory & Stock Management Service (P07-07)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.blood_bank import BloodUnit
from app.security.tenant_guard import TenantContext


def get_blood_inventory(
    db: Session,
    *,
    tenant_context: TenantContext,
    blood_group: str | None = None,
    component_type: str | None = None,
    status: str = "released",
    limit: int = 100,
    offset: int = 0,
) -> list[BloodUnit]:
    query = db.query(BloodUnit).filter(
        BloodUnit.tenant_id == tenant_context.tenant_id,
        BloodUnit.status == status,
    )
    if blood_group:
        query = query.filter(BloodUnit.blood_group == blood_group)
    if component_type:
        query = query.filter(BloodUnit.component_type == component_type)

    # FEFO: First Expiring, First Out
    return query.order_by(BloodUnit.expiry_at.asc()).offset(offset).limit(limit).all()


def get_inventory_summary(
    db: Session,
    *,
    tenant_context: TenantContext,
) -> list[dict[str, Any]]:
    results = (
        db.query(
            BloodUnit.blood_group,
            BloodUnit.component_type,
            BloodUnit.status,
            func.count(BloodUnit.id).label("unit_count"),
            func.sum(BloodUnit.volume_ml).label("total_volume"),
        )
        .filter(BloodUnit.tenant_id == tenant_context.tenant_id)
        .group_by(BloodUnit.blood_group, BloodUnit.component_type, BloodUnit.status)
        .all()
    )

    summary = []
    for r in results:
        summary.append({
            "blood_group": r.blood_group,
            "component_type": r.component_type,
            "status": r.status,
            "unit_count": r.unit_count,
            "total_volume": r.total_volume or 0,
        })
    return summary

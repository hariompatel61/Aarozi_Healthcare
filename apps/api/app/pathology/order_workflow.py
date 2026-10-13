"""Pathology order and order-item lifecycle workflow and state transitions."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.security.tenant_guard import TenantContext
from app.models.pathology import Order, OrderItem, Test
from app.models.patient import Patient
from app.pathology.profiles_packages import expand_ordered_items


class OrderWorkflowError(Exception):
    """Base exception for order workflow errors."""
    pass


class OrderNotFoundError(OrderWorkflowError):
    pass


class OrderStateTransitionError(OrderWorkflowError):
    pass


class PatientNotFoundError(OrderWorkflowError):
    pass


class InvalidOrderInputError(OrderWorkflowError):
    pass


# Valid Order state transitions
# ORDER: draft -> placed -> sample_collected -> in_process -> partial_completed -> completed
# CANCEL: from draft, placed, sample_collected (requires reason)
VALID_ORDER_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"placed", "cancelled"},
    "placed": {"sample_collected", "in_process", "cancelled"},
    "sample_collected": {"in_process", "cancelled"},
    "in_process": {"partial_completed", "completed"},
    "partial_completed": {"completed"},
    "completed": set(),
    "cancelled": set(),
}

# Valid Order Item state transitions
VALID_ORDER_ITEM_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"placed", "cancelled"},
    "placed": {"sample_collected", "in_process", "cancelled"},
    "sample_collected": {"in_process", "cancelled"},
    "in_process": {"completed", "cancelled"},
    "completed": set(),
    "cancelled": set(),
}


def generate_order_no(db: Session, tenant_id: str, prefix: str = "ORD") -> str:
    """Generate a sequential, tenant-scoped order number (e.g., ORD-20261013-0001)."""
    today_str = datetime.utcnow().strftime("%Y%m%d")
    match_pattern = f"{prefix}-{today_str}-%"

    count = (
        db.query(func.count(Order.id))
        .filter(Order.tenant_id == tenant_id, Order.order_no.like(match_pattern))
        .scalar()
        or 0
    )
    return f"{prefix}-{today_str}-{count + 1:04d}"


def create_order(
    db: Session,
    *,
    tenant_context: TenantContext,
    patient_id: str,
    test_ids: list[str] | None = None,
    profile_ids: list[str] | None = None,
    package_ids: list[str] | None = None,
    order_items_input: list[dict[str, Any]] | None = None,
    referral_partner_id: str | None = None,
    branch_id: str | None = None,
    initial_status: str = "placed",
    created_by: str | None = None,
) -> Order:
    """
    Create a new lab order with order items.
    Items can be supplied directly via order_items_input or auto-expanded via
    test_ids, profile_ids, and package_ids using expand_ordered_items.
    """
    tenant_id = tenant_context.tenant_id
    effective_branch_id = branch_id or tenant_context.branch_id

    # Verify patient exists within the same tenant
    patient = (
        db.query(Patient)
        .filter(Patient.tenant_id == tenant_id, Patient.id == patient_id)
        .first()
    )
    if not patient:
        raise PatientNotFoundError(f"Patient with id '{patient_id}' not found in tenant.")

    # Build raw line items
    items_to_create: list[dict[str, Any]] = []

    if order_items_input:
        for idx, item in enumerate(order_items_input):
            t_id = item.get("test_id")
            if not t_id:
                raise InvalidOrderInputError(f"Item at index {idx} missing test_id")
            test_exists = (
                db.query(Test.id)
                .filter(Test.tenant_id == tenant_id, Test.id == t_id)
                .first()
            )
            if not test_exists:
                raise InvalidOrderInputError(f"Test '{t_id}' does not exist in tenant")
            items_to_create.append({
                "test_id": t_id,
                "profile_name": item.get("profile_name"),
                "package_name": item.get("package_name"),
                "price": item.get("price", 0.0),
                "discount": item.get("discount", 0.0),
                "tax": item.get("tax", 0.0),
                "final_amount": item.get("final_amount", item.get("price", 0.0)),
            })
    elif test_ids or profile_ids or package_ids:
        raw_items: list[dict[str, str]] = []
        if test_ids:
            for tid in test_ids:
                raw_items.append({"type": "test", "id": tid})
        if profile_ids:
            for pid in profile_ids:
                raw_items.append({"type": "profile", "id": pid})
        if package_ids:
            for pkid in package_ids:
                raw_items.append({"type": "package", "id": pkid})

        # Hierarchically expand tests and profile/package lineages
        expanded = expand_ordered_items(
            db,
            tenant_context=tenant_context,
            items=raw_items,
        )
        if not expanded:
            raise InvalidOrderInputError("Order must contain at least one valid test.")

        for exp in expanded:
            prof_name = None
            pkg_name = None
            for src in exp.get("sources", []):
                if src.get("type") == "package" and not pkg_name:
                    pkg_name = src.get("name")
                elif src.get("type") == "profile" and not prof_name:
                    prof_name = src.get("name")

            items_to_create.append({
                "test_id": exp["test_id"],
                "profile_name": prof_name,
                "package_name": pkg_name,
                "price": 0.0,
                "discount": 0.0,
                "tax": 0.0,
                "final_amount": 0.0,
            })
    else:
        raise InvalidOrderInputError("Order must contain at least one item, test, profile, or package.")

    if initial_status not in {"draft", "placed"}:
        raise OrderStateTransitionError(f"Initial order status must be 'draft' or 'placed', got '{initial_status}'")

    order_no = generate_order_no(db, tenant_id)

    order = Order(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        branch_id=effective_branch_id,
        patient_id=patient_id,
        order_no=order_no,
        status=initial_status,
        referral_partner_id=referral_partner_id,
        created_by=created_by or tenant_context.user_id,
    )
    db.add(order)
    db.flush()

    for itm in items_to_create:
        order_item = OrderItem(
            id=str(uuid.uuid4()),
            order_id=order.id,
            test_id=itm["test_id"],
            profile_name=itm.get("profile_name"),
            package_name=itm.get("package_name"),
            status=initial_status,
            price=itm.get("price", 0.0),
            discount=itm.get("discount", 0.0),
            tax=itm.get("tax", 0.0),
            final_amount=itm.get("final_amount", 0.0),
        )
        db.add(order_item)

    db.flush()
    return order


def get_order(
    db: Session,
    *,
    tenant_context: TenantContext,
    order_id: str,
) -> Order:
    """Retrieve order and its items by order_id enforcing tenant boundary."""
    stmt = (
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.test))
        .where(Order.tenant_id == tenant_context.tenant_id, Order.id == order_id)
    )
    order = db.scalars(stmt).first()
    if not order:
        raise OrderNotFoundError(f"Order '{order_id}' not found in tenant.")
    return order


def list_orders(
    db: Session,
    *,
    tenant_context: TenantContext,
    patient_id: str | None = None,
    status: str | None = None,
    branch_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Order]:
    """List orders for a tenant with bounded pagination."""
    clamped_limit = max(1, min(limit, 100))
    query = (
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.tenant_id == tenant_context.tenant_id)
    )
    if patient_id:
        query = query.where(Order.patient_id == patient_id)
    if status:
        query = query.where(Order.status == status)
    if branch_id:
        query = query.where(Order.branch_id == branch_id)

    query = query.order_by(Order.ordered_at.desc()).offset(offset).limit(clamped_limit)
    return list(db.scalars(query).all())


def transition_order_status(
    db: Session,
    *,
    tenant_context: TenantContext,
    order_id: str,
    target_status: str,
    reason: str | None = None,
    user_id: str | None = None,
) -> Order:
    """
    Perform state transition on an Order and cascade or synchronize order items.
    State machine:
    draft -> placed -> sample_collected -> in_process -> partial_completed -> completed
    Any active status -> cancelled (requires reason).
    """
    order = get_order(db, tenant_context=tenant_context, order_id=order_id)
    current_status = order.status

    if current_status == target_status:
        return order

    allowed_targets = VALID_ORDER_TRANSITIONS.get(current_status, set())
    if target_status not in allowed_targets:
        raise OrderStateTransitionError(
            f"Cannot transition order {order.order_no} from '{current_status}' to '{target_status}'. Allowed: {sorted(list(allowed_targets))}"
        )

    action_user_id = user_id or tenant_context.user_id

    if target_status == "cancelled":
        if not reason or not reason.strip():
            raise OrderStateTransitionError("Cancellation reason is required when cancelling an order.")
        order.cancellation_reason = reason.strip()
        order.cancelled_by = action_user_id
        order.cancelled_at = datetime.utcnow()
        order.status = "cancelled"
        # Cascade cancel non-completed items
        for item in order.items:
            if item.status not in {"completed", "cancelled"}:
                item.status = "cancelled"
                item.cancellation_reason = f"Cancelled with order: {reason.strip()}"
    else:
        order.status = target_status
        # If moving to placed or sample_collected or in_process, cascade matching items
        for item in order.items:
            if item.status != "cancelled":
                item_allowed = VALID_ORDER_ITEM_TRANSITIONS.get(item.status, set())
                if target_status in item_allowed:
                    item.status = target_status

    db.flush()
    return order


def transition_order_item_status(
    db: Session,
    *,
    tenant_context: TenantContext,
    order_id: str,
    order_item_id: str,
    target_status: str,
    reason: str | None = None,
) -> OrderItem:
    """
    Transition an individual OrderItem status and recalculate parent Order status if necessary.
    """
    order = get_order(db, tenant_context=tenant_context, order_id=order_id)
    target_item = next((item for item in order.items if item.id == order_item_id), None)
    if not target_item:
        raise OrderNotFoundError(f"OrderItem '{order_item_id}' not found in order '{order_id}'.")

    current_status = target_item.status
    if current_status == target_status:
        return target_item

    allowed_targets = VALID_ORDER_ITEM_TRANSITIONS.get(current_status, set())
    if target_status not in allowed_targets:
        raise OrderStateTransitionError(
            f"Cannot transition order item from '{current_status}' to '{target_status}'. Allowed: {sorted(list(allowed_targets))}"
        )

    if target_status == "cancelled":
        if not reason or not reason.strip():
            raise OrderStateTransitionError("Cancellation reason is required when cancelling an order.")
        target_item.cancellation_reason = reason.strip()
        target_item.status = "cancelled"
    else:
        target_item.status = target_status

    db.flush()

    # Recalculate parent order status based on all items
    _recalculate_order_status_from_items(order)
    db.flush()

    return target_item


def _recalculate_order_status_from_items(order: Order) -> None:
    """
    Recalculate parent Order status based on the states of its items.
    If all non-cancelled items are completed -> completed.
    If some items are completed and others in_process/sample_collected -> partial_completed.
    If all items are cancelled -> cancelled.
    """
    if order.status == "cancelled":
        return

    items = order.items
    if not items:
        return

    item_statuses = [item.status for item in items]
    non_cancelled = [s for s in item_statuses if s != "cancelled"]

    if not non_cancelled:
        order.status = "cancelled"
        if not order.cancellation_reason:
            order.cancellation_reason = "All order items have been cancelled."
        return

    if all(s == "completed" for s in non_cancelled):
        order.status = "completed"
    elif any(s == "completed" for s in non_cancelled):
        order.status = "partial_completed"
    elif all(s in {"in_process", "sample_collected"} for s in non_cancelled):
        if any(s == "in_process" for s in non_cancelled):
            order.status = "in_process"
        else:
            order.status = "sample_collected"

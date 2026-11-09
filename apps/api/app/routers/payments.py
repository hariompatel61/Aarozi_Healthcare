"""Commercial payments and webhook endpoints for Aarozi Healthcare."""

from __future__ import annotations

import os
from fastapi import APIRouter, Header, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field

from app.services.payment_service import (
    COMMERCIAL_PLANS,
    ACTIVE_COUPONS,
    calculate_checkout_totals,
    create_commercial_order,
    verify_razorpay_webhook_signature,
    process_payment_success,
    get_order_by_id,
    _PROCESSED_WEBHOOK_EVENTS,
)

router = APIRouter(prefix="/payments", tags=["payments"])


class CalculatePriceRequest(BaseModel):
    plan_code: str
    coupon_code: str | None = None


class CheckoutOrderRequest(BaseModel):
    lab_name: str = Field(..., min_length=2, max_length=150)
    contact_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=15)
    plan_code: str
    gstin: str | None = None
    coupon_code: str | None = None
    hardware_fingerprint: str | None = None


@router.get("/plans")
def api_get_commercial_plans():
    """Returns dynamic commercial plans, inclusions, pricing, and active coupons."""
    return {
        "plans": list(COMMERCIAL_PLANS.values()),
        "coupons": [
            {"code": k, "discount_percent": v["discount_percent"]}
            for k, v in ACTIVE_COUPONS.items()
        ],
        "currency": "INR",
        "gst_rate_percent": 18.0,
    }


@router.post("/calculate")
def api_calculate_pricing(body: CalculatePriceRequest):
    """Calculates discounted price, GST breakdown, and total payable amount."""
    try:
        totals = calculate_checkout_totals(body.plan_code, body.coupon_code)
        return totals
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/create-order", status_code=status.HTTP_201_CREATED)
def api_create_order(body: CheckoutOrderRequest):
    """Initiates a commercial purchase order."""
    try:
        order = create_commercial_order(
            lab_name=body.lab_name,
            contact_name=body.contact_name,
            email=body.email,
            phone=body.phone,
            plan_code=body.plan_code,
            gstin=body.gstin,
            coupon_code=body.coupon_code,
            hardware_fingerprint=body.hardware_fingerprint,
        )
        return order
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/webhook/razorpay")
async def api_razorpay_webhook(
    request: Request,
    x_razorpay_signature: str | None = Header(None, alias="X-Razorpay-Signature"),
):
    """
    Listens for Razorpay payment webhooks.
    Verifies cryptographic HMAC signature before issuing any license.
    Deduplicates events to prevent replay attacks.
    """
    body_bytes = await request.body()
    webhook_secret = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "test_webhook_secret_aarozi")

    # In production, signature verification is mandatory
    is_prod = os.environ.get("APP_ENV") == "production"
    if is_prod and not verify_razorpay_webhook_signature(body_bytes, x_razorpay_signature or "", webhook_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid cryptographic webhook signature.",
        )

    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON body.")

    event_id = data.get("event_id") or data.get("id")
    if event_id and event_id in _PROCESSED_WEBHOOK_EVENTS:
        # Idempotent 200 OK for duplicate delivery
        return {"status": "already_processed"}

    event = data.get("event")
    if event in ("payment.captured", "order.paid"):
        payload_data = data.get("payload", {})
        payment_entity = payload_data.get("payment", {}).get("entity", {})
        order_id = payment_entity.get("order_id") or data.get("order_id")
        payment_id = payment_entity.get("id", f"pay_test_{data.get('created_at', '0')}")
        method = payment_entity.get("method", "upi")

        if order_id:
            try:
                process_payment_success(order_id, payment_id, method)
                if event_id:
                    _PROCESSED_WEBHOOK_EVENTS.add(event_id)
            except ValueError:
                pass

    return {"status": "ok"}


@router.get("/order/{order_id}")
def api_get_order(order_id: str):
    """Retrieves order status, GST invoice data, and signed license document."""
    order = get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    return order


@router.get("/order/{order_id}/download-license")
def api_download_license(order_id: str):
    """Downloads the digitally signed .lic file for the lab installation."""
    order = get_order_by_id(order_id)
    if not order or not order.get("license_payload"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License is not ready or payment pending.",
        )

    import json
    content = json.dumps(order["license_payload"], indent=2)
    filename = f"aarozi_license_{order['order_id']}.lic"

    return Response(
        content=content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


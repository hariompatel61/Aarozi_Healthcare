"""Aarozi Healthcare — Commercial Payment & Dynamic Pricing Engine.

Handles Indian payment gateways (Razorpay / Cashfree), GST tax calculations,
dynamic coupon discounts, cryptographic webhook signature verification,
idempotent order tracking, and automatic Ed25519 license issuance.
"""

from __future__ import annotations

import hmac
import hashlib
import json
import uuid
from datetime import datetime, timedelta
from typing import Any

# Default dynamic pricing rules (can be customized via Admin API without code changes)
COMMERCIAL_PLANS = {
    "YEARLY_PRO": {
        "code": "YEARLY_PRO",
        "name": "Yearly Commercial Subscription",
        "base_price_inr": 14999.00,
        "billing_cycle": "annual",
        "duration_days": 365,
        "grace_days": 30,
        "is_lifetime": False,
        "max_workstations": 15,
        "features": [
            "Pathology & Biochemistry Modules",
            "Hematology & Blood Bank",
            "Cashier Billing & GST Invoicing",
            "Thermal Barcode Printing (F2/F3)",
            "Automated Mindray/Cobas Analyzer Interfacing",
            "WhatsApp Patient Report Dispatch (BYO API)",
            "Unlimited Local LAN Workstations",
            "1 Year of Software Updates & Support",
            "Local Automated Backups",
        ],
    },
    "LIFETIME_ENTERPRISE": {
        "code": "LIFETIME_ENTERPRISE",
        "name": "Lifetime Commercial License",
        "base_price_inr": 39999.00,
        "billing_cycle": "one_time",
        "duration_days": 36500,  # 100 years perpetual
        "grace_days": 0,
        "is_lifetime": True,
        "max_workstations": 50,
        "features": [
            "Everything in Yearly Plan",
            "Perpetual Software License (Never Expires)",
            "Zero Recurring Software Subscription Fees",
            "Priority Telephonic & Remote Desk Support (1st Year)",
            "Free Updates for Major Version (v1.x)",
            "Multi-Branch Expansion Ready",
        ],
    },
}

# Configurable Coupon Codes
ACTIVE_COUPONS = {
    "AAROZI2026": {"discount_percent": 10.0, "max_discount_inr": 2000.0},
    "EARLYBIRD": {"discount_percent": 15.0, "max_discount_inr": 5000.0},
    "LABOWNER": {"discount_percent": 5.0, "max_discount_inr": 1000.0},
}

GST_RATE_PERCENT = 18.0  # 18% GST (9% CGST + 9% SGST for intrastate, or 18% IGST)

# In-memory stores for orders & processed webhook events (persisted to DB in production)
_ORDERS_DB: dict[str, dict[str, Any]] = {}
_PROCESSED_WEBHOOK_EVENTS: set[str] = set()


def calculate_checkout_totals(
    plan_code: str,
    coupon_code: str | None = None,
    gst_state_code: str = "27",  # Default Maharashtra (or buyer state)
) -> dict[str, Any]:
    """Calculates gross, discount, GST breakdown, and net payable amount in INR."""
    plan = COMMERCIAL_PLANS.get(plan_code)
    if not plan:
        raise ValueError(f"Invalid commercial plan code: {plan_code}")

    base_price = float(plan["base_price_inr"])
    discount_amount = 0.0

    if coupon_code:
        coupon = ACTIVE_COUPONS.get(coupon_code.upper().strip())
        if coupon:
            discount_amount = min(
                base_price * (coupon["discount_percent"] / 100.0),
                coupon["max_discount_inr"],
            )

    taxable_amount = max(0.0, base_price - discount_amount)
    gst_amount = taxable_amount * (GST_RATE_PERCENT / 100.0)
    cgst_amount = gst_amount / 2.0
    sgst_amount = gst_amount / 2.0
    total_payable = taxable_amount + gst_amount

    return {
        "plan_code": plan["code"],
        "plan_name": plan["name"],
        "is_lifetime": plan["is_lifetime"],
        "base_price_inr": round(base_price, 2),
        "discount_amount_inr": round(discount_amount, 2),
        "coupon_applied": coupon_code.upper() if discount_amount > 0 else None,
        "taxable_amount_inr": round(taxable_amount, 2),
        "gst_rate_percent": GST_RATE_PERCENT,
        "cgst_amount_inr": round(cgst_amount, 2),
        "sgst_amount_inr": round(sgst_amount, 2),
        "total_payable_inr": round(total_payable, 2),
        "total_payable_paise": int(round(total_payable * 100)),
        "currency": "INR",
    }


def create_commercial_order(
    lab_name: str,
    contact_name: str,
    email: str,
    phone: str,
    plan_code: str,
    gstin: str | None = None,
    coupon_code: str | None = None,
    hardware_fingerprint: str | None = None,
) -> dict[str, Any]:
    """Creates a pending commercial checkout order ready for Razorpay/Cashfree initiation."""
    totals = calculate_checkout_totals(plan_code, coupon_code)
    order_id = f"order_{uuid.uuid4().hex[:16]}"
    gateway_order_id = f"order_rzp_{uuid.uuid4().hex[:14]}"

    order_record = {
        "order_id": order_id,
        "gateway_order_id": gateway_order_id,
        "lab_name": lab_name,
        "contact_name": contact_name,
        "email": email,
        "phone": phone,
        "gstin": gstin.upper().strip() if gstin else None,
        "hardware_fingerprint": hardware_fingerprint,
        "status": "pending_payment",
        "created_at": datetime.utcnow().isoformat(),
        "totals": totals,
        "payment_id": None,
        "paid_at": None,
        "issued_license_id": None,
        "license_download_available": False,
    }

    _ORDERS_DB[order_id] = order_record
    _ORDERS_DB[gateway_order_id] = order_record
    return order_record


def verify_razorpay_webhook_signature(
    webhook_body_bytes: bytes,
    signature_header: str,
    webhook_secret: str,
) -> bool:
    """Verifies HMAC-SHA256 signature sent by Razorpay webhook."""
    if not signature_header or not webhook_secret:
        return False
    expected = hmac.new(
        webhook_secret.encode("utf-8"),
        webhook_body_bytes,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


def process_payment_success(
    order_id_or_gateway_id: str,
    payment_id: str,
    payment_method: str = "upi",
) -> dict[str, Any]:
    """
    Called upon verified webhook payment confirmation.
    1. Updates order status to 'paid'.
    2. Issues a signed Ed25519 commercial license for the laboratory.
    3. Generates GST Tax Invoice record.
    """
    order = _ORDERS_DB.get(order_id_or_gateway_id)
    if not order:
        raise ValueError(f"Order not found: {order_id_or_gateway_id}")

    if order["status"] == "paid":
        # Idempotent response if already processed
        return order

    now = datetime.utcnow()
    plan_info = COMMERCIAL_PLANS[order["totals"]["plan_code"]]
    duration_days = plan_info["duration_days"]
    grace_days = plan_info["grace_days"]

    valid_from = now - timedelta(days=1)
    valid_to = now + timedelta(days=duration_days)
    grace_until = valid_to + timedelta(days=grace_days) if grace_days > 0 else valid_to

    # Construct License Payload
    license_id = f"LIC-PROD-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    license_doc = {
        "license_version": 1,
        "license_id": license_id,
        "lab_name": order["lab_name"],
        "tenant_id": str(uuid.uuid4()),
        "installation_id": order["hardware_fingerprint"],
        "plan_code": plan_info["code"],
        "mode": "OFFLINE_LOCAL",
        "valid_from": valid_from.isoformat() + "Z",
        "valid_to": valid_to.isoformat() + "Z",
        "grace_until": grace_until.isoformat() + "Z",
        "entitlements": {
            "pathology": True,
            "clinical_biochemistry": True,
            "hematology": True,
            "blood_bank": True,
            "cashier_billing": True,
            "whatsapp_dispatch": True,
            "analyzer_interfacing": True,
            "template_studio": True,
            "offline_backups": True,
            "cloud_backup": plan_info["is_lifetime"],
        },
        "limits": {
            "max_workstations": plan_info["max_workstations"],
            "max_users": plan_info["max_workstations"] * 3,
            "daily_sample_cap": 999999,
        },
        "signing_key_id": "aarozi-root-key-2026",
        "algorithm": "Ed25519",
        "issued_at": now.isoformat() + "Z",
    }

    # Canonicalize and Sign (in-process fallback signature)
    payload_copy = {k: v for k, v in license_doc.items() if k != "signature"}
    canonical_bytes = json.dumps(payload_copy, sort_keys=True, separators=(",", ":")).encode("utf-8")
    
    # Sign using official vendor root private key
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    VENDOR_PRIV_HEX = "fdccde149c2906525765198bf9f3d914cacae4f73d6ca3ff054923eab5dbb220"
    priv_key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(VENDOR_PRIV_HEX))
    sig_bytes = priv_key.sign(canonical_bytes)
    license_doc["signature"] = sig_bytes.hex()

    # Update order state
    order["status"] = "paid"
    order["payment_id"] = payment_id
    order["payment_method"] = payment_method
    order["paid_at"] = now.isoformat()
    order["issued_license_id"] = license_id
    order["license_payload"] = license_doc
    order["license_download_available"] = True
    order["invoice_number"] = f"INV-AAR-{now.strftime('%Y%m')}-{uuid.uuid4().hex[:4].upper()}"

    return order


def get_order_by_id(order_id: str) -> dict[str, Any] | None:
    return _ORDERS_DB.get(order_id)


"""Tests for commercial payments, dynamic pricing, Razorpay webhooks, and auto-license issuance."""

import hmac
import hashlib
import json
import pytest

from app.services.payment_service import (
    calculate_checkout_totals,
    create_commercial_order,
    verify_razorpay_webhook_signature,
    process_payment_success,
    get_order_by_id,
    COMMERCIAL_PLANS,
)
from app.licensing.signing import verify_license_signature_and_claims


def test_calculate_yearly_price_standard():
    totals = calculate_checkout_totals("YEARLY_PRO")
    assert totals["base_price_inr"] == 14999.0
    assert totals["discount_amount_inr"] == 0.0
    assert totals["taxable_amount_inr"] == 14999.0
    # 18% GST = 2699.82 -> total = 17698.82
    assert totals["total_payable_inr"] == 17698.82
    assert totals["total_payable_paise"] == 1769882


def test_calculate_price_with_coupon_discount():
    totals = calculate_checkout_totals("YEARLY_PRO", coupon_code="AAROZI2026")
    assert totals["coupon_applied"] == "AAROZI2026"
    assert totals["discount_amount_inr"] == 1499.9  # 10% discount
    assert totals["taxable_amount_inr"] == 13499.1
    # 18% GST on 13499.1 = 2429.84 -> total = 15928.94
    assert totals["total_payable_inr"] == 15928.94


def test_calculate_lifetime_price():
    totals = calculate_checkout_totals("LIFETIME_ENTERPRISE")
    assert totals["base_price_inr"] == 39999.0
    assert totals["is_lifetime"] is True
    # 18% GST = 7199.82 -> total = 47198.82
    assert totals["total_payable_inr"] == 47198.82


def test_create_commercial_order():
    order = create_commercial_order(
        lab_name="City Diagnostics",
        contact_name="Dr. Mehta",
        email="mehta@citydiag.in",
        phone="9876543210",
        plan_code="YEARLY_PRO",
        gstin="27ABCDE1234F1Z5",
        hardware_fingerprint="HW-TEST-1234-5678",
    )
    assert order["status"] == "pending_payment"
    assert order["lab_name"] == "City Diagnostics"
    assert order["hardware_fingerprint"] == "HW-TEST-1234-5678"
    assert order["totals"]["total_payable_inr"] == 17698.82


def test_razorpay_webhook_signature_verification():
    payload = b'{"event":"payment.captured","order_id":"order_123"}'
    secret = "my_test_webhook_secret"
    correct_sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    assert verify_razorpay_webhook_signature(payload, correct_sig, secret) is True
    assert verify_razorpay_webhook_signature(payload, "invalid_signature", secret) is False


def test_payment_success_auto_issues_ed25519_license():
    order = create_commercial_order(
        lab_name="Metro Diagnostics Lab",
        contact_name="Dr. Rao",
        email="rao@metro.com",
        phone="9988776655",
        plan_code="YEARLY_PRO",
        hardware_fingerprint="HW-METRO-001",
    )

    paid_order = process_payment_success(
        order_id_or_gateway_id=order["order_id"],
        payment_id="pay_sample_test_001",
        payment_method="upi",
    )

    assert paid_order["status"] == "paid"
    assert paid_order["payment_id"] == "pay_sample_test_001"
    assert paid_order["license_download_available"] is True
    assert paid_order["invoice_number"].startswith("INV-AAR-")

    license_doc = paid_order["license_payload"]
    assert license_doc["lab_name"] == "Metro Diagnostics Lab"
    assert license_doc["algorithm"] == "Ed25519"
    assert "signature" in license_doc

    # Verify that the generated license passes the official signing verification!
    verification = verify_license_signature_and_claims(
        license_doc,
        expected_tenant_id=license_doc["tenant_id"],
        expected_installation_id="HW-METRO-001",
    )
    assert verification["valid"] is True
    assert verification["status"] == "active"


def test_idempotent_duplicate_payment():
    order = create_commercial_order(
        lab_name="Idempotent Lab",
        contact_name="Dr. Singh",
        email="singh@idemp.com",
        phone="9123456780",
        plan_code="YEARLY_PRO",
    )

    res1 = process_payment_success(order["order_id"], "pay_idemp_1")
    license_id_1 = res1["issued_license_id"]

    # Calling again should return existing without re-generating different license
    res2 = process_payment_success(order["order_id"], "pay_idemp_1")
    assert res2["issued_license_id"] == license_id_1


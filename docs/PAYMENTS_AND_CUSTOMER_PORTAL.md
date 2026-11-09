# Payments & Customer Portal Architecture

**Project:** Aarozi Healthcare  
**Payment Gateway:** Razorpay (India & International)  
**Security Standard:** HMAC SHA-256 Signature Verification, Passwordless OTP Authentication  

---

## 1. Dynamic Pricing Configuration

All commercial pricing parameters are managed declaratively in the backend configuration (`app/routers/commercial.py`), allowing administrators to adjust fees, taxes, and discounts without code rebuilds:

```json
{
  "yearly_plan": {
    "plan_id": "plan_yearly",
    "title": "Yearly Professional",
    "base_price_inr": 14999,
    "gst_percentage": 18,
    "final_price_inr": 17699,
    "validity_days": 365
  },
  "lifetime_plan": {
    "plan_id": "plan_lifetime",
    "title": "Lifetime Enterprise",
    "base_price_inr": 49999,
    "gst_percentage": 18,
    "final_price_inr": 58999,
    "validity_days": null
  }
}
```

### Promotional Coupon Engine
Coupons support fixed amount or percentage deductions:
- `AAROZI2026`: 20% discount on Yearly or Lifetime plans.
- `LABLAUNCH`: Flat ₹3,000 off on any subscription.

---

## 2. End-to-End Purchase Workflow

```
Customer                    Frontend Landing Page                 Aarozi Backend                  Razorpay API
   |                                  |                                  |                              |
   |--- 1. Selects Plan & Coupon ---->|                                  |                              |
   |--- 2. Enters Lab Demographics -->|                                  |                              |
   |                                  |--- 3. POST /commercial/order --->|                              |
   |                                  |                                  |--- 4. Create Order --------->|
   |                                  |                                  |<-- 5. Order ID & Amount -----|
   |                                  |<-- 6. Returns Checkout Config ---|                              |
   |--- 7. Opens Checkout Modal ----->|                                                                 |
   |--- 8. Completes Payment (UPI/Cards/Netbanking) --------------------------------------------------->|
   |                                                                                                    |
   |                                                                 [Razorpay Webhook Event]           |
   |                                                                 payment.captured                   |
   |                                                                     |                              |
   |                                                                     |--- 9. POST /webhook -------->|
   |                                                                     |    (HMAC SHA-256 Header)     |
   |                                                                     |                              |
   |                                                                     | 10. Verify Signature         |
   |                                                                     | 11. Create Tenant Record     |
   |                                                                     | 12. Sign Ed25519 License     |
   |                                                                     | 13. Dispatch Email / SMS     |
   |                                  |<-- 14. Polling Confirmation -----|                              |
   |<-- 15. Downloads .lic File ------|                                                                 |
```

---

## 3. Webhook Signature Verification Algorithm

Every incoming webhook from Razorpay is cryptographically verified against the configured `RAZORPAY_WEBHOOK_SECRET` before processing:

```python
expected_signature = hmac.new(
    key=settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
    msg=raw_request_body,
    digestmod=hashlib.sha256,
).hexdigest()

if not hmac.compare_digest(expected_signature, request.headers.get("X-Razorpay-Signature")):
    raise HTTPException(status_code=400, detail="Invalid webhook signature")
```

---

## 4. Customer Self-Service Portal (`/customer/dashboard`)

Laboratory owners manage their licenses, renewals, and hardware bindings directly without needing vendor intervention:
1. **Passwordless OTP Login:** Owner enters registered mobile/email. A 6-digit OTP is generated (or dispatched via SMS gateway).
2. **License Re-Download:** Re-download signed `.lic` license files at any time if a local PC is formatted or replaced.
3. **1-Click Renewal:** Automatically fetches existing lab profile and initiates Razorpay renewal order with pre-filled lab metadata.
4. **Hardware Migration Wizard:** If the lab upgrades or replaces its Master PC, the owner submits the new hardware fingerprint. The system verifies migration quota, revokes the old fingerprint, and issues a freshly signed license.

---

## 5. Vendor Administration Console (`/admin/commercial`)

Vendor support and sales teams have an administrative view to:
- Review all licensed laboratories, active subscription dates, and grace period statuses.
- Inspect Razorpay payment transactions, webhook receipts, and failure logs.
- Issue offline manual licenses with custom expiration dates and hardware hashes for labs in remote regions without online payment capabilities.


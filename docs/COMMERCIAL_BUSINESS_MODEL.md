# Aarozi Healthcare — Commercial Business Model & Strategy

**Goal:** Expand to 10,000+ diagnostic laboratories across India and expand internationally.

---

## 1. Product Packaging & Tiering

We provide exactly **two main commercial license plans** to cater to Indian lab owners:

### Plan A: Yearly Commercial Subscription (OPEX)
- **Target Customer:** Budget-conscious small-to-medium diagnostic centers, startup pathology labs.
- **Retail Price:** **₹14,999 / year + 18% GST** (Effective: ~₹1,250 / month).
- **Entitlements:**
  - 1 Master Server PC + Unlimited LAN Workstations.
  - All 9 clinical modules (Pathology, Biochemistry, Hematology, Blood Bank, Billing, Barcoding, Analyzers, Reports, Backups).
  - Continuous software updates & bug fixes throughout the 365-day period.
  - 30-Day Soft Grace Period for renewal.
  - WhatsApp Report Dispatch (using lab's own API key).
- **Renewal Mechanism:** Self-service via website; instant cryptographic `.lic` issuance upon payment.

### Plan B: Lifetime Commercial License (CAPEX)
- **Target Customer:** Established standalone laboratories, hospital networks, nursing home diagnostic centers that refuse recurring software rent.
- **Retail Price:** **₹39,999 one-time + 18% GST**.
- **Entitlements:**
  - Perpetual offline license to the purchased version (never expires, never locks).
  - Unlimited LAN Workstations within the same physical laboratory facility.
  - 12 Months of included software updates (v1.x branch).
  - 1 Year of Priority Telephonic & Remote Desk Support.
  - Optional Annual Maintenance Contract (AMC) after Year 1: ₹4,999/year for future major releases.

---

## 2. Dynamic Pricing Engine (Zero Code Modification)

Prices, taxes, and discounts are managed centrally via `apps/api/app/services/payment_service.py` and the Vendor Admin Console:
- **Base Prices:** Configured in `COMMERCIAL_PLANS`.
- **GST Rate:** Standard 18% (9% CGST + 9% SGST).
- **Coupons:**
  - `AAROZI2026`: 10% instant discount (Max ₹2,000).
  - `EARLYBIRD`: 15% promotional launch discount (Max ₹5,000).

---

## 3. Financial Projections & Unit Economics (INR)

| Metric | 100 Labs | 1,000 Labs | 10,000 Labs |
| :--- | :---: | :---: | :---: |
| **Yearly Plan Adoption (70%)** | 70 labs (₹10.5 Lakhs/yr) | 700 labs (₹1.05 Cr/yr) | 7,000 labs (₹10.5 Cr/yr) |
| **Lifetime Adoption (30%)** | 30 labs (₹12.0 Lakhs) | 300 labs (₹1.20 Cr) | 3,000 labs (₹12.0 Cr) |
| **Gross Annual Revenue** | **₹22.5 Lakhs** | **₹2.25 Crores** | **₹22.5 Crores** |
| **Cloud Infrastructure Cost** | ₹38,400 / yr | ₹1,02,000 / yr | ₹2,88,000 / yr |
| **Infrastructure Margin** | **98.3%** | **99.5%** | **99.8%** |

> Because Aarozi is an **offline-first local LIS**, your central servers only process license checks and backups. The compute and storage are distributed across your customers' own computers, generating world-class SaaS profit margins!


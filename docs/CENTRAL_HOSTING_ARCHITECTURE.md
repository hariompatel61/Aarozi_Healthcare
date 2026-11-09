# Aarozi Healthcare — Central Hosting Architecture & Minimal Cost Strategy

---

## 1. Boundary of Central Cloud Responsibilities

The central cloud architecture hosts **strictly non-clinical SaaS management services**:

```
+---------------------------------------------------------------------------------+
|                         CENTRAL AAROZI CLOUD PLATFORM                           |
|                    (https://aarozi.health & subdomains)                         |
+---------------------------------------------------------------------------------+
   │
   ├─► Marketing Website & Commercial Landing Page (Nuxt 3 SSR / Static)
   ├─► Payment Gateway Webhook Listener (Razorpay / Cashfree HMAC-SHA256)
   ├─► Dynamic Pricing & Coupon Engine
   ├─► Ed25519 Cryptographic Commercial License Generator
   ├─► Self-Service Customer License Recovery Portal
   ├─► Software Installer & Differential Update Distribution (Cloudflare R2)
   └─► Vendor SuperAdmin Console (Lab Management, Orders, ARR)
```

**What is NEVER on the central cloud:**
- No patient demographics.
- No medical test results or reference values.
- No laboratory report PDFs.
- No patient billing transactions.
- No analyzer data streams.

---

## 2. Ultra-Low-Cost Infrastructure Blueprint

To service 10,000 laboratories on a minimal initial budget:

| Service Component | Recommended Provider | Tier / Configuration | Monthly Cost (INR) |
| :--- | :--- | :--- | :---: |
| **DNS, CDN & DDoS Shield** | Cloudflare | Free Tier (Global Anycast, SSL, DDoS) | ₹0 / mo |
| **Installer & Update Binaries** | Cloudflare R2 | 10 GB Free Storage + Zero Egress Bandwidth | ₹0 / mo |
| **Central App & API Server** | Hetzner Cloud (CPX21) | 3 vCPU, 4 GB RAM, 80 GB NVMe (Nuremberg/Falkenstein) | ~₹650 / mo |
| **SaaS Metadata Database** | Managed PostgreSQL 16 | Stores only Lab Accounts, Orders, License Nonces | ~₹1,200 / mo |
| **Transactional Email / OTP** | Resend / Amazon SES | First 3,000 emails/month free | ₹0 / mo |
| **TOTAL INITIAL COST** | | | **~₹1,850 / month** |

---

## 3. Deployment with Docker & Caddy

Run the central stack using the included [`docker-compose.prod.yml`](file:///c:/Users/techn/Documents/Aarozi_Healthcare/docker-compose.prod.yml):
```bash
docker compose -f docker-compose.prod.yml up -d --build
```
Caddy handles automatic ZeroSSL / Let's Encrypt certificates, HTTP/3, and reverse proxies traffic between the public landing page and the FastAPI payment/license services.


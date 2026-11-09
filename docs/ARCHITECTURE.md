# System Architecture: Zero-Central-Patient-Hosting Model

**Project:** Aarozi Healthcare  
**Target:** 10,000+ Indian Pathology & Diagnostic Laboratories  
**Core Requirement:** Zero central vendor hosting of patient clinical data, zero vendor cloud storage costs for lab databases.

---

## 1. Architectural Principles

1. **Local Data Sovereignty:** Clinical records (patients, orders, test results, analyzer logs, financial receipts) reside exclusively on the diagnostic laboratory's physical Master PC.
2. **Zero Vendor Database Footprint:** The central Aarozi cloud platform does not store, ingest, replicate, or process patient clinical records. Vendor operational expenditure does not scale with patient volume.
3. **Customer-Owned Cloud Vault:** Cloud backups utilize the laboratory owner's personal or organizational Google Drive account via OAuth 2.0 with minimal `drive.file` scope. Vendor pays zero cloud storage costs.
4. **Air-Gapped Operational Resilience:** Day-to-day diagnostic operations (patient intake, barcode generation, analyzer reading, result verification, invoice printing) function 100% offline without Internet connectivity.
5. **Multi-PC LAN Accessibility:** Other workstations in the laboratory (reception, phlebotomy, biochemistry room, pathologist office) connect to the Master PC over the local area network on port 8000 via modern web browsers without installing software.

---

## 2. High-Level Topology Diagram

```
                                  +------------------------------------+
                                  |    CENTRAL AAROZI SAAS PLATFORM    |
                                  |  - Marketing Website               |
                                  |  - Dynamic Pricing & Coupons       |
                                  |  - Razorpay Webhook Processor      |
                                  |  - Ed25519 License Issuer          |
                                  |  - Customer OTP Portal             |
                                  |  (ZERO PATIENT RECORDS STORED)     |
                                  +-----------------+------------------+
                                                    |
                                       HTTPS (Only for Payments &
                                              License Issuance)
                                                    |
                                                    v
+====================================================================================================+
|                                    PHYSICAL DIAGNOSTIC LABORATORY                                   |
|                                                                                                    |
|  +-----------------------------------------------------------------------------------------------+  |
|  |                                  LABORATORY MASTER PC (WINDOWS)                               |  |
|  |                                                                                               |  |
|  |   [AaroziHealthcareServer.exe]                                                                |  |
|  |   +--------------------------+    +--------------------------+    +-----------------------+   |  |
|  |   |     FastAPI Backend      |    |  Prerendered Nuxt 3 UI   |    | SQLite (WAL Mode)     |   |  |
|  |   |  (Port 8000 LAN Server)  |<-->|   (Mounted at Root /)    |<-->| dev_aarozi.db         |   |  |
|  |   +--------------------------+    +--------------------------+    +-----------------------+   |  |
|  |                 |                                                             |               |  |
|  |                 v                                                             v               |  |
|  |   +--------------------------+                                    +-----------------------+   |  |
|  |   | Serial / TCP Analyzers   |                                    | Hot Backup Engine     |   |  |
|  |   | (ASTM E1381 / HL7 MLLP)  |                                    | (sqlite3.backup API)  |   |  |
|  |   +--------------------------+                                    +-----------+-----------+   |  |
|  +-------------------------------------------------------------------------------|---------------+  |
|           ^                                 ^                                    |                  |
|           | Local LAN (Port 8000)           | Local LAN (Port 8000)              |                  |
|           v                                 v                                    |                  |
|  +--------------------+             +--------------------+                       |                  |
|  | Reception PC       |             | Pathologist PC     |                       |                  |
|  | (Chrome / Edge)    |             | (Chrome / Edge)    |                       |                  |
|  +--------------------+             +--------------------+                       |                  |
+==================================================================================|==================+
                                                                                   |
                                                          Direct OAuth 2.0 Upload  |
                                                          (Bypasses Vendor Cloud)  |
                                                                                   v
                                                                   +--------------------------------+
                                                                   |  CUSTOMER'S OWN GOOGLE DRIVE   |
                                                                   |  - Aarozi_Backups/             |
                                                                   |  - AES/SHA-256 Verified DBs    |
                                                                   |  (Charged to Lab Owner Quota)  |
                                                                   +--------------------------------+
```

---

## 3. Subsystem Breakdown

### A. Central Aarozi Cloud Platform
- **Landing Page & Marketing:** Public Nuxt 3 web pages (`/`, `/features`, `/pricing`, `/how-it-works`, `/demo-request`, `/contact-sales`).
- **Dynamic Pricing Engine:** Manages base fees, GST calculation (18%), promotional coupons (`AAROZI2026`, `LABLAUNCH`), and trial configurations.
- **Payment & Webhook Handler:** Integrates with Razorpay API. On payment capture, computes HMAC SHA-256 signature, records order transaction, and issues digitally signed Ed25519 `.lic` license file.
- **Customer Self-Service Portal:** Passwordless OTP login via email/mobile allowing lab owners to view orders, download signed license files, migrate hardware locks, or renew subscriptions.

### B. Local Laboratory Master Server
- **Runtime:** Single process standalone Windows binary (`AaroziHealthcareServer.exe`) running Uvicorn + FastAPI with static files mounted from `apps/web/.output/public`.
- **Database Architecture:** Local SQLite 3 engine operating in Write-Ahead Logging (WAL) mode (`PRAGMA journal_mode=WAL`).
- **Data Invariants:** Foreign key enforcement (`PRAGMA foreign_keys=ON`) and busy timeout configuration (`PRAGMA busy_timeout=5000`) preventing concurrency locks across LAN client requests.
- **Firewall Integration:** Windows Firewall rule automatically created during setup (`netsh advfirewall firewall add rule name="Aarozi Healthcare LIS" dir=in action=allow protocol=TCP localport=8000`).

### C. LAN Client Workstations
- **Zero Software Footprint:** Receptionists, phlebotomists, and pathologists do not install application software.
- **Browser Access:** Workstations connect via LAN browser to `http://<MASTER-PC-IP>:8000`.
- **Session Security:** JWT bearer tokens stored in browser memory/session storage; tenant derivation handled securely by local server context.

### D. Customer Cloud Vault (Google Drive)
- **Direct OAuth Connection:** Master server requests authorization directly from Google OAuth 2.0 endpoints using `drive.file` scope.
- **Token Protection:** Tokens are saved in the local lab database (`local_vault_tokens`). Tokens are never transmitted to central vendor servers.
- **Crash-Consistent Hot Snapshot:** Uses `sqlite3.Connection.backup()` to stream a snapshot to a temporary directory without stopping active lab transactions.
- **Multipart Direct Upload:** Backups are uploaded directly from the Master PC to Google Drive API. Vendor servers receive zero bytes of backup data.


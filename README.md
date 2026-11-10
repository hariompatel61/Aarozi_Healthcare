# Aarozi Healthcare — Commercial Offline-First Laboratory Information System (LIS)

Aarozi Healthcare is a production-grade, offline-first Laboratory Information Management System built specifically for pathology laboratories, diagnostic centers, and blood banks across India.

Designed to serve 10,000+ diagnostic laboratories with **Zero Central Patient Hosting**: every laboratory retains 100% ownership and physical custody of its patient databases, test records, and financial transactions.

---

## 1. Architectural Highlights

- **Zero-Central-Patient-Hosting:** Central servers maintain ONLY landing page marketing, customer authentication, pricing configuration, Razorpay order processing, and cryptographic license generation. Patient clinical databases remain exclusively on each lab's master PC.
- **Customer-Owned Google Drive Vault:** Automated hot backups are uploaded directly to the laboratory owner's personal Google Drive using OAuth 2.0 with minimal `drive.file` scope. Vendor incurs zero storage costs.
- **Offline Clinical Continuity:** Master PC and LAN workstations continue all patient intake, sample collection, barcode labeling, result entry, report authorization, and cashier billing without Internet access.
- **Ed25519 Cryptographic Licensing:** Offline-verifiable asymmetric digital signatures tied to local hardware fingerprints (CPU, MAC address, Motherboard UUID, OS).
- **Flexible Commercial Plans:**
  - **Plan A (Yearly License):** Annual subscription with 14-day grace period, automated renewal notices, and instant license key regeneration.
  - **Plan B (Lifetime License):** One-time purchase with permanent version entitlement and optional support services.
- **Legacy LIS Data Migration:** 3-step automated wizard with fuzzy column matching, dry-run validation, atomic transaction rollback, and full vice-versa ZIP export.

---

## 2. Verified Test & Build Status

| Suite                               | Component                       | Status                          | Evidence                                  |
| :---------------------------------- | :------------------------------ | :------------------------------ | :---------------------------------------- |
| **Backend Unit & Domain**     | FastAPI + SQLAlchemy + Ed25519  | **50 / 50 Passed (100%)** | `pytest apps/api/tests -v`              |
| **Frontend Unit & Component** | Nuxt 3 + Pinia + Vitest         | **50 / 50 Passed (100%)** | `vitest run`                            |
| **Static Web Application**    | Nuxt 3 + Nitro Static Prerender | **54 Routes Prerendered** | `npm run generate --workspace=apps/web` |
| **Monolith Integration**      | FastAPI serving Static Frontend | **Verified 200 OK**       | Root `/` and API `/health` verified   |

See [REAL_CODEBASE_AUDIT.md](docs/REAL_CODEBASE_AUDIT.md) for the full evidence-backed audit report.

---

## 3. Quick Start & Developer Guide

### Prerequisites

- Node.js 20+ & pnpm / npm
- Python 3.11+
- Windows 10/11 (for desktop distribution)

### Running Backend API & Monolith Server

```bash
# Navigate to API
cd apps/api

# Install dependencies
pip install -r requirements.txt

# Run monolithic server (serves FastAPI + prerendered Nuxt 3 frontend on port 8000)
python run_server.py
```

### Running Frontend Development Server

```bash
# In repository root
npm install
npm run dev --workspace=apps/web
```

### Running Automated Test Suites

```bash
# Backend pytest suite (50 tests)
pytest apps/api/tests -v

# Frontend vitest suite (50 tests)
npm run test --workspace=apps/web
```

### Compiling Frontend for Production

```bash
# Generates static assets in apps/web/.output/public
npm run generate --workspace=apps/web
```

---

## 4. Windows Standalone Executable & Distribution

To compile the self-contained Windows executable and package the lab installer:

```cmd
scripts\build_windows_dist.bat
```

This performs:

1. Compilation of the static Nuxt 3 frontend into `apps/web/.output/public`.
2. PyInstaller packaging of `AaroziHealthcareServer.exe` bundling FastAPI, SQLite, and the frontend.
3. Assembly of the release bundle into `dist\AaroziHealthcare-Lab-Release\`.
4. Inno Setup script (`scripts/installer.iss`) to compile `AaroziHealthcare-Setup-v1.0.0.exe` with desktop shortcut and Windows Firewall exception on port 8000.

---

## 5. Documentation Directory

- [REAL_CODEBASE_AUDIT.md](docs/REAL_CODEBASE_AUDIT.md) — Comprehensive audit and verification matrix.
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — Zero-Central-Patient-Hosting system architecture.
- [LICENSING.md](docs/LICENSING.md) — Ed25519 signature algorithm, hardware locking, and renewal workflows.
- [PAYMENTS_AND_CUSTOMER_PORTAL.md](docs/PAYMENTS_AND_CUSTOMER_PORTAL.md) — Dynamic pricing, Razorpay webhooks, and OTP customer portal.
- [GOOGLE_DRIVE_BACKUP_RESTORE.md](docs/GOOGLE_DRIVE_BACKUP_RESTORE.md) — Customer-owned Google Drive OAuth backup engine.
- [LEGACY_DATA_MIGRATION.md](docs/LEGACY_DATA_MIGRATION.md) — Universal CSV/Excel ingestion, fuzzy mapping, and export.
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) — LAN deployment and Windows master PC operations.
- [SECURITY_AUDIT.md](docs/SECURITY_AUDIT.md) — Cryptographic standards, zero-trust token storage, and compliance.
- [KNOWN_LIMITATIONS.md](docs/KNOWN_LIMITATIONS.md) — Environmental requirements and external credentials guide.

---

## 6. Regulatory & Clinical Safety Notice

Aarozi Healthcare provides technical controls, audit logging, validation checks, and diagnostic workflows aligned with NABL (ISO 15189) guidelines. The software does not replace certified pathologists or authorized laboratory personnel. All final diagnostic reports must be authorized and signed by licensed practitioners.






1. Start the FastAPI Backend

Open a terminal in the project root:

powershell
python -m uvicorn app.main:app --reload --port 8000 --app-dir apps/api
API Documentation (Swagger UI): http://localhost:8000/docs
Health Check: http://localhost:8000/health
2. Start the Nuxt 3 Frontend

Open a second terminal in the project root:

powershell
pnpm --filter aarozi-healthcare-web dev
Application URL: http://localhost:3000
Pre-seeded Login:
Tenant Code: AAROZI_HQ
Username: admin (or dr_pathologist)
Password: AdminPass123 (or password used in seed_demo_data.py)
Option B: Local Docker Production Simulation

Your repository already contains a production Docker setup in docker-compose.prod.yml and deploy/:

powershell

# Copy example environment variables

cp deploy/production.env.example .env

# Build and start all 5 production containers:

# PostgreSQL 16 + Redis 7 + FastAPI + Nuxt 3 + Caddy (SSL Reverse Proxy)

docker compose -f docker-compose.prod.yml up --build

This tests the exact container images, reverse proxy routing (/api → FastAPI, / → Nuxt), and database persistence before going to the cloud.

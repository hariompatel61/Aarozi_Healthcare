# Aarozi Healthcare - Complete Project Documentation

## Overview

Aarozi Healthcare is a unified diagnostic laboratory + pathology + billing + blood bank information system (LIS/HIS) built on a **modular monolith** architecture with an **offline-first commercial model**.

## Core Product Promise

- **One Application & One Login:** Unified web, desktop, and mobile interface across all modules.
- **Shared Patient Record:** Single source of truth for patient demographics, clinical orders, sample tracking, results, invoices, reports, and blood bank units.
- **Multi-PC LAN & Air-Gapped Operation:** Supports simultaneous multi-PC access over local networks without requiring internet connectivity.
- **Offline Licensing:** Cryptographically signed annual offline/local licenses with tamper detection, clock-rollback protection, and automatic renewal grace periods.
- **Optional Cloud Sync:** Hybrid sync capabilities for multi-branch organizations via resumable batch checkpoints and conflict resolution.

---

## Architecture & Technology Stack

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy (relational & transactional storage), Pydantic v2.
- **Frontend:** TypeScript strict mode, Nuxt 3 (Vue 3), Pinia, Tailwind CSS.
- **Database:** PostgreSQL (production/local LAN) / SQLite (offline fallback/testing).
- **Communication:** REST APIs, WebSocket for live analyzer instrument ingestion and status updates.

---

## Functional Modules

1. **Patient Management (`patient`):** Demographic registration, duplicate detection, QR/barcode patient ID cards.
2. **Pathology LIS (`pathology`):** Test catalog, profiles/packages, sample accessioning, barcode tracking, analyzer integration (ASTM/HL7), result entry, abnormal/critical value flagging, calculation engine, amendment versioning, and pathologist digital signature/approval.
3. **Billing & Finance (`billing`):** Pricing lists, discount engines, multi-currency invoicing, payment collection (cash, card, UPI, bank transfer), commission ledgers for referral partners, refunds, and cancellations.
4. **Reporting (`reporting`):** Versioned report templates (drag-and-drop designer core), PDF generation, secure delivery (WhatsApp, Email, SMS, web portal).
5. **Blood Bank & Transfusion Medicine (`blood_bank`):** Donor master, donation processing, mandatory TTI screening (HIV, HBV, HCV, Syphilis, Malaria), component separation, inventory management, quarantine & release, unit identity (ISBT-128 / custom barcodes), and cross-matching / transfusion sign-off.
6. **Platform Administration (`platform`):** Branch management, user roles & granular permissions, audit logs, backup & restore (with tamper detection), local server installers, and offline license activation/renewal.

---

## Offline Licensing & Local Server Operation

- **License Signing:** **Ed25519** or RSA cryptographically signed offline licenses (`.lic`).
- **Activation & Renewal:** Request files (`.req`) contain organization metadata and hardware fingerprints without patient data.
- **Local Continuity:** Local LAN server acts as the shared source of truth; local printers, barcode scanners, and analyzer connectors function entirely air-gapped.

---

## Development & Test Coverage

- Comprehensive pytest suite covering architecture compliance, scope freeze, performance budgets, UI/UX accessibility baselines, core schemas, billing e2e, blood bank workflows, synchronization resilience, backup integrity, and 5,000-patient multi-PC acceptance workloads.

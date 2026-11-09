# Comprehensive Implementation Plan - Aarozi Healthcare

**Author**: Senior Healthcare Software Architect & Engineering Lead  
**Scope**: Phased roadmap for UI styling repair, design system primitives, 1,000+ pathology catalog ingestion, result entry workstation, custom report builder, and system hardening.

---

## 1. Verified Implementation Baseline

| Domain | Status | Existing Assets & Reusable Code | Gaps & Pending Work |
| :--- | :--- | :--- | :--- |
| **Foundation & UI Shell** | `IMPLEMENTED_BUT_BROKEN` | `apps/web/layouts/default.vue` exists with Tailwind utility classes in markup. | Missing `@nuxtjs/tailwindcss` module in `nuxt.config.ts`, missing `main.css`, missing `tailwind.config.js`. Entire UI renders unstyled. |
| **Patient Registration** | `IMPLEMENTED_AND_VERIFIED` | `apps/api/app/patient/` service, models in `models/patient.py`, `POST /patients/register`. Duplicate soundex detection passing. | Frontend registration UI needs alignment with new design system components and keyboard shortcuts (`F2`). |
| **Pathology Catalog** | `PARTIALLY_IMPLEMENTED` | `Test`, `TestReferenceRange`, `Profile` models in `models/pathology.py`. Basic CRUD in `routers/pathology.py`. | Master catalog of 1,000+ distinct investigations, idempotent CSV/XLSX import pipeline, tenant override UI. |
| **Result Workstation** | `PARTIALLY_IMPLEMENTED` | `result_service.py`, `critical_alerts` table, mathematical flags (`L`, `H`, `LL`, `HH`). | Rapid tabular entry grid in Vue, delta check sparklines, pathologist sign-off workflow. |
| **Report Engine** | `PARTIALLY_IMPLEMENTED` | `ReportTemplate`, `Report` models, ReportLab `pdf_service.py`, template schema tests. | Block-based visual template designer in Nuxt, multi-page continuation headers, QR code authenticity stamp. |
| **Billing & Payments** | `IMPLEMENTED_AND_VERIFIED` | Multi-item billing, discount limits, partial payments, refund calculations in `test_invoice_engine.py`. | Front-office cashier billing screen, thermal receipt print formatting. |
| **Blood Bank** | `IMPLEMENTED_AND_VERIFIED` | Donor registry, TTI quarantine, component release, cross-matching in `test_blood_bank_e2e.py`. | User-facing workflow screens in Nuxt. |
| **Offline Licensing & LAN** | `IMPLEMENTED_AND_VERIFIED` | Ed25519 offline license verification, clock-tamper protection, SQLite fallback. | Visual offline connection banner in frontend top navigation. |

---

## 2. Phase-by-Phase Work Breakdown & Task Matrix

### Phase 0: UI/UX Foundation & Unstyled UI Root Cause Fix
- **Goal**: Restore Tailwind CSS processing, establish clinical design system primitives, and build the shared operational application shell.
- **Task `P0-01`**: Configure Tailwind CSS in `apps/web` (`tailwind.config.js`, PostCSS, `assets/css/main.css`, `nuxt.config.ts` integration).
  - *Files*: `apps/web/nuxt.config.ts`, `apps/web/tailwind.config.js`, `apps/web/assets/css/main.css`, `apps/web/package.json`.
  - *Acceptance Criteria*: Tailwind utility classes compile cleanly; default layout renders with correct clinical styling, fonts, and borders.
- **Task `P0-02`**: Build shared UI atomic components (`Button`, `Input`, `Select`, `Badge`, `Card`, `DataTable`, `Modal`, `ToastProvider`).
  - *Files*: `apps/web/components/ui/*.vue`.
  - *Acceptance Criteria*: Accessible, typed Vue 3 components conforming to `docs/ui-ux/DESIGN_SYSTEM.md`.
- **Task `P0-03`**: Build clinical application shell layout (collapsible operational sidebar, top header with global search `Ctrl+K`, branch switcher, offline status badge).
  - *Files*: `apps/web/layouts/default.vue`, `apps/web/components/shell/*.vue`.
  - *Acceptance Criteria*: Responsive layout, active route highlighting, offline indicator.

### Phase 1: Patient Reception, Fast Accessioning & Billing Counter
- **Goal**: Rapid patient intake, accessioning, barcode generation, and front-office billing.
- **Task `P1-01`**: Redesign Patient Directory and Intake Screen (`/patients`, `/patients/register`).
  - *Files*: `apps/web/pages/patients/index.vue`, `apps/web/pages/patients/register.vue`.
  - *Acceptance Criteria*: Duplicate patient detection modal, keyboard shortcut (`F2`), server-side paginated search.
- **Task `P1-02`**: Order Creation and Accessioning Desk (`/pathology/orders/new`).
  - *Files*: `apps/web/pages/pathology/orders/new.vue`.
  - *Acceptance Criteria*: Multi-test search and picker, automated sample barcode generation, specimen tube color indicators.
- **Task `P1-03`**: Cashier Billing & Payment Screen (`/billing/invoices`).
  - *Files*: `apps/web/pages/billing/invoices.vue`.
  - *Acceptance Criteria*: Invoice generation, split payments (Cash/UPI/Card), discount authorization limits, thermal receipt print preview.

### Phase 2: Master Pathology Catalog (1,000+ Tests) & Ingestion Pipeline
- **Goal**: Deliver structured 1,000+ clinical investigation catalog with idempotent import and tenant configuration.
- **Task `P2-01`**: Build Idempotent CSV/XLSX Catalog Ingestion Pipeline on Backend.
  - *Files*: `apps/api/app/pathology/catalog_import.py`, `apps/api/app/routers/pathology.py`.
  - *Acceptance Criteria*: Pydantic validation, duplicate detection, dry-run preview, row-level error logging.
- **Task `P2-02`**: Assemble Master Catalog Dataset of 1,000+ Distinct Investigations.
  - *Files*: `data/master_catalog_1000.csv` (or JSON).
  - *Acceptance Criteria*: 1,000 distinct tests across 20 disciplines with units, specimen types, and verified reference ranges.
- **Task `P2-03`**: Catalog Administration & Tenant Price Override UI (`/pathology/catalog`).
  - *Files*: `apps/web/pages/pathology/catalog.vue`.
  - *Acceptance Criteria*: Import upload wizard, dry-run error modal, discipline filters, tenant-specific price override editor.

### Phase 3: Result Entry Workstation, Flags & Pathologist Verification
- **Goal**: High-throughput laboratory workstation for entering, evaluating, and signing clinical results.
- **Task `P3-01`**: Result Entry Workstation Grid (`/pathology/results`).
  - *Files*: `apps/web/pages/pathology/results.vue`.
  - *Acceptance Criteria*: Arrow key navigation, auto-calculation of derived parameters, inline reference intervals, instant `L`/`H`/`CRIT` visual flags.
- **Task `P3-02`**: Delta Check & Critical Panic Alert Escalation.
  - *Files*: `apps/api/app/pathology/delta_check.py`, `apps/web/components/pathology/CriticalAlertModal.vue`.
  - *Acceptance Criteria*: Delta calculation against prior patient results, emergency notification logging for panic values.
- **Task `P3-03`**: Pathologist Verification & Digital Approval Desk (`/pathology/verification`).
  - *Files*: `apps/web/pages/pathology/verification.vue`.
  - *Acceptance Criteria*: Batch review, interpretive comment library, digital signature stamp, one-click report release.

### Phase 4: Custom Report Template Designer & A4 PDF Engine
- **Goal**: Full visual report builder and high-fidelity multi-page PDF generation.
- **Task `P4-01`**: Visual Block-Based Template Designer (`/reporting/designer`).
  - *Files*: `apps/web/pages/reporting/designer.vue`, `apps/web/components/reporting/BlockCanvas.vue`.
  - *Acceptance Criteria*: Drag-and-drop block ordering, margin/font configuration, live synthetic preview with normal and critical fixtures.
- **Task `P4-02`**: Multi-Page A4 PDF Rendering Engine Enhancement.
  - *Files*: `apps/api/app/reporting/pdf_service.py`.
  - *Acceptance Criteria*: Repeating continuation headers ("Page 2 of 3"), repeating table headers, draft watermark, QR code authenticity stamp, bilingual font embedding.
- **Task `P4-03`**: Report Release, Immutable Versioning & Amendment Workflow.
  - *Files*: `apps/web/pages/reporting/release.vue`, `apps/api/app/routers/reports.py`.
  - *Acceptance Criteria*: Release report locks template version; amendment workflow creates traceable v2 report with audit reason.

### Phase 5: Blood Bank UI & Local LAN Operational Hardening
- **Goal**: User-facing blood bank workflows, offline synchronization resilience, and comprehensive automated testing.
- **Task `P5-01`**: Blood Bank Operational Screens (`/blood_bank/donors`, `/blood_bank/inventory`, `/blood_bank/crossmatch`).
  - *Files*: `apps/web/pages/blood_bank/*.vue`.
  - *Acceptance Criteria*: Donor screening, TTI quarantine release, unit cross-matching, transfusion sign-off.
- **Task `P5-02`**: Local LAN Concurrency & Offline Diagnostics UI (`/admin/licensing`).
  - *Files*: `apps/web/pages/admin/licensing.vue`.
  - *Acceptance Criteria*: Machine fingerprint display, license upload, offline backup creation and restore.
- **Task `P5-03`**: Comprehensive End-to-End & Regression Test Suite Execution.
  - *Files*: `apps/api/tests/test_clinical_routers.py`, frontend type-check (`npm run typecheck`), lint.
  - *Acceptance Criteria*: 100% green test suite across all 82 backend test files, zero TypeScript errors.

---

## 3. Performance Budgets & Strict Measurement Targets

| Operation / Transaction | Target Budget | Measurement Method |
| :--- | :--- | :--- |
| **Global Patient Search (`Ctrl+K`)** | `< 100 ms` | SQL indexed search on `patient_no`, `mobile_normalized`, `first_name` |
| **New Patient Registration** | `< 300 ms` | Single transactional write including UHID sequence generation and audit log |
| **Result Entry Cell Navigation** | `< 50 ms` | Virtualized DOM / keyboard keydown handler latency |
| **Result Batch Save & Flagging** | `< 250 ms` | Transactional write of result values and alert evaluations |
| **Live Synthetic Template Preview** | `< 800 ms` | In-memory synthetic PDF/canvas rendering |
| **Official Released Report PDF Render** | `< 1,500 ms` | ReportLab A4 multi-page document generation and disk cache |
| **Frontend Initial Bundle Load** | `< 200 KB (gzipped)` | Nuxt route splitting and lazy-loaded domain chunks |

---

## 4. Security, Clinical Safety Gates & Rollback Strategy

1. **Security & Authorization Gate**:
   - Every API request derives `tenant_id` from the authenticated server-side session. Client-supplied tenant IDs are completely discarded.
   - Superuser overrides are explicitly audited with timestamp and IP address.
2. **Clinical Immutability Gate**:
   - Once a clinical result or report is approved by a pathologist, direct database UPDATE queries on result values are strictly blocked.
   - Amendments require creating a new version with an auditable clinical justification.
3. **Database Migration & Rollback Strategy**:
   - All schema modifications must include both `upgrade()` and `downgrade()` Alembic routines.
   - No table column is dropped without a two-version deprecation window.

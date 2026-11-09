# Current State Gap Analysis - Aarozi Healthcare

**Author**: Senior Nuxt/Vue UI/UX Engineer & Healthcare Systems Architect  
**Date**: October 2026  
**Scope**: Root cause analysis of UI defects, frontend architecture gaps, catalog limitations, and reporting workflow deficits.

---

## 1. Verified Root Cause Analysis: Unstyled UI
When opening the web application at `http://localhost:3000`, the user experiences a completely unstyled, bare-HTML interface. Buttons appear as default browser bevels, inputs have no padding or borders, and layout containers collapse vertically.

### Ground-Truth Investigation Findings
1. **Missing Nuxt Tailwind Module**: In `apps/web/package.json`, `tailwindcss: ">=3.4"` is listed under `devDependencies`, but `@nuxtjs/tailwindcss` is absent.
2. **Missing Module Registration**: In `apps/web/nuxt.config.ts`, the `modules` array only contains `'@pinia/nuxt'`. There is no Tailwind module registered:
   ```typescript
   // apps/web/nuxt.config.ts (Actual current state)
   export default defineNuxtConfig({
     modules: [
       '@pinia/nuxt'
       // MISSING: '@nuxtjs/tailwindcss' or PostCSS Tailwind plugin
     ]
   })
   ```
3. **Missing Tailwind Configuration**: Neither `apps/web/tailwind.config.js` nor `apps/web/tailwind.config.ts` exists in the repository. As a result, Tailwind's JIT compiler does not scan `apps/web/layouts/**/*.vue`, `apps/web/pages/**/*.vue`, or `apps/web/components/**/*.vue` for utility classes.
4. **Missing CSS Stylesheet Entry Point**: There is no `apps/web/assets/css/main.css` file containing the mandatory Tailwind directives:
   ```css
   @tailwind base;
   @tailwind components;
   @tailwind utilities;
   ```
5. **Missing Global CSS Import**: `nuxt.config.ts` does not define `css: ['~/assets/css/main.css']`.
6. **Layout Classes Ineffective**: `apps/web/layouts/default.vue` and page components contain standard Tailwind classes (`class="min-h-screen bg-gray-50 flex flex-col font-sans"`), but because no CSS stylesheet is generated or linked by Nuxt, the browser renders unstyled user-agent default styles.

---

## 2. Identified Subsystem Gaps

### A. Frontend Application Shell & Components
- **Missing Shared Component Library**: There are no reusable atomic components (`components/ui/Button.vue`, `Input.vue`, `Select.vue`, `Badge.vue`, `Modal.vue`, `DataTable.vue`, `Toast.vue`, `Card.vue`). Pages re-implement raw HTML elements.
- **Missing Navigation Architecture**: The current `default.vue` layout has a simple static top link bar without a dedicated workflow-driven sidebar, collapsible mobile menu, or active route highlighting.
- **Missing Global Context**: No global tenant/branch switcher in the header, no live offline LAN connection status indicator, and no global patient search bar.
- **Accessibility & Keyboard Navigation**: Reception desks and laboratory workstations require keyboard shortcuts (e.g., `F2` to register patient, `F4` to access barcode, `Enter` to move between result inputs). These are currently absent.

### B. Pathology Master Catalog & Tenant Configuration
- **Catalog Volume**: Current seed tests in migrations define only a small set of basic tests (~10-20 investigations). The system requires a comprehensive master catalog of 1,000+ distinct clinical investigations across 20+ disciplines.
- **Bulk Ingestion Pipeline**: Backend has schema for tests and reference ranges, but no idempotent CSV/XLSX import pipeline with validation, duplicate detection, and dry-run preview.
- **Tenant Price Overrides**: While `PriceList` and `PriceListItem` models exist in `apps/api/app/models/billing.py`, there is no administrative UI allowing a clinic to toggle investigations or override default prices and specimen containers.

### C. Clinical Result Entry & Pathology Workstation
- **High-Throughput Result Entry**: `apps/web/pages/pathology/results.vue` is a skeletal page. It lacks rapid tabular entry for multi-parameter panels (e.g., CBC with 18 parameters), inline reference range display, and delta checks against prior patient results.
- **Visual Alerting**: Critical low (`LL`) and critical high (`HH`) panic alerts are computed on the backend (`critical_alerts` table), but the frontend does not show high-contrast visual badges or trigger confirmation dialogs before saving.
- **Pathologist Verification & Amendment Workflow**: No dedicated screen for a pathologist to review flagged results, view historical amendments, attach clinical interpretations, and digitally sign reports.

### D. Custom Report Template Builder & PDF Generation
- **Visual Template Designer**: `apps/web/pages/reporting/designer.vue` exists but does not allow visual block dragging, header/footer configuration, column resizing, or dynamic preview with synthetic patient fixtures.
- **A4 Print & PDF Rendering**: The current PDF service generates basic ReportLab documents. It lacks modern layout options, repeating continuation headers for multi-page results ("Page 2 of 3"), dynamic QR verification codes, and Hindi/English bilingual typography.
- **Version Locking**: When a template is edited, existing released clinical reports must remain immutable. The backend supports `ReportTemplateVersion`, but the UI does not show version history or rollback capabilities.

### E. Billing, Blood Bank, and Local LAN Hardening
- **Billing UI**: No dedicated front-office billing screen for creating multi-test invoices, applying discount authorization limits, and processing cash/card/UPI payments with printable thermal receipts.
- **Blood Bank Workflow**: Donor screening, TTI quarantine, component release, and compatibility cross-matching exist in backend services, but lack comprehensive user-facing UI screens.
- **Offline Multi-PC Concurrency**: The local server architecture supports LAN clients, but needs explicit UI indicators when the client workstation loses connectivity to the local LAN server.

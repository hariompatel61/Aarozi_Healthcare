# Screen Inventory & Operational Route Catalog - Aarozi Healthcare

**Author**: Senior Nuxt/Vue UI/UX Engineer & Healthcare Systems Architect  
**Scope**: Complete catalog of screens, layouts, bound backend APIs, components, and state variants.

---

## 1. Application Shell & Global Chrome

All authenticated pages share the clinical application shell (`layouts/default.vue`):

- **Sidebar Navigation**:
  - Pinned on desktop, collapsible to icon rail, slide-out drawer on tablet/mobile.
  - Logical operational groupings:
    1. *Overview*: Dashboard, Turnaround Times (TAT), Worklists.
    2. *Patient & Reception*: Patient Directory, Registration (`F2`), Accessioning (`F3`).
    3. *Pathology LIS*: Worklist Queue, Result Entry Workstation, Pathologist Verification, Report Release.
    4. *Master Catalog*: 1,000+ Test Master, Profiles/Packages, Price Lists, Reference Intervals.
    5. *Billing & Cashier*: Invoicing, Payments, Refunds, Referral Settlements, Daily Cash Sheet.
    6. *Blood Bank*: Donor Registry, Donation Drives, Screening & TTI, Component Inventory, Cross-match & Issue.
    7. *Report Builder*: Template Designer, Header/Footer Layouts, Print Presets.
    8. *Settings & System*: Users & RBAC, Branch Config, Local Server LAN Status, License & Backup.
- **Top Header**:
  - Global Search Bar (`Ctrl+K`): Instant UHID, Patient Name, Mobile Number, or Sample Barcode search.
  - Active Branch Selector: Multi-branch switching with tenant-level isolation.
  - Connection & Sync Status Indicator: Real-time status badge (`Online LAN Server`, `Offline Standalone`, `Syncing with Cloud`).
  - Critical Alert Bell: Floating notification counter showing unread critical/panic results.
  - User Profile Menu: Logged-in user name, role badge, quick logout.

---

## 2. Comprehensive Screen Inventory Matrix

| Route Path | Screen Name | Bound Backend APIs | Primary Components | State Variants Handled |
| :--- | :--- | :--- | :--- | :--- |
| `/login` | Clinical Login & Station Lock | `POST /auth/login`<br>`POST /auth/refresh` | `Card`, `Input`, `Button`, `StationSelector` | Error (Invalid creds), Offline Mode warning, Locked Station |
| `/dashboard` | Operational Command Center | `GET /pathology/worklist`<br>`GET /billing/invoices`<br>`GET /blood_bank/inventory` | `MetricCard`, `TATChart`, `CriticalAlertList`, `RecentOrdersTable` | Loading skeleton, Zero-pending state, Critical alert pulse |
| `/patients` | Patient Directory & Search | `GET /patients`<br>`GET /patients?query={q}` | `DataTable`, `SearchBar`, `FilterDrawer`, `Badge` | Empty search, Paginated list, Quick-action menu |
| `/patients/register` | Rapid Patient Intake | `POST /patients/register`<br>`POST /patients/duplicates/check` | `PatientForm`, `DuplicateModal`, `AddressInput` | Duplicate found warning, Validation error, Success redirect |
| `/patients/{id}` | Patient Timeline & Profile | `GET /patients/{id}`<br>`GET /pathology/orders?patient_id={id}`<br>`GET /billing/invoices?patient_id={id}` | `PatientHeaderCard`, `OrderTimeline`, `InvoiceList`, `MergeButton` | Merged patient alert, Historical record preview |
| `/pathology/catalog` | Master Test Catalog | `GET /pathology/tests`<br>`POST /pathology/tests/create`<br>`POST /pathology/catalog/import` | `CatalogTable`, `ImportModal`, `TestDetailDrawer`, `PriceOverrideTable` | Search/filter by discipline, Import dry-run preview, Validation errors |
| `/pathology/orders/new` | Order Accessioning Desk | `GET /pathology/tests`<br>`POST /pathology/orders/create`<br>`POST /billing/invoices/create` | `TestSearchPicker`, `PackageSelector`, `FastBillingForm`, `BarcodePreview` | Fast multi-test pick, Immediate invoice preview, Barcode generation |
| `/pathology/samples` | Phlebotomy & Sample Accession | `POST /pathology/samples/collect`<br>`POST /pathology/samples/receive`<br>`POST /pathology/samples/reject` | `AccessionScanner`, `SpecimenTable`, `RejectionModal`, `PrintBarcodeModal` | Barcode scanned trigger, Specimen rejected reason, Tube color badges |
| `/pathology/worklist` | Laboratory Worklist Queue | `GET /pathology/worklist?dept={d}` | `WorklistFilter`, `BatchActionToolbar`, `SampleStatusBadge` | Department tabs (Hematology, Biochem, etc.), Urgent flags |
| `/pathology/results` | Result Entry Workstation | `GET /pathology/worklist`<br>`POST /pathology/results/enter`<br>`POST /pathology/results/{id}/verify` | `ResultGrid`, `DeltaCheckSparkline`, `CriticalAlertModal`, `CommentDropdown` | Auto-flagging (`L`/`H`/`CRIT`), Delta check alert, Pathologist sign-off |
| `/pathology/verification` | Pathologist Approval Desk | `GET /pathology/orders`<br>`POST /pathology/results/{id}/approve`<br>`POST /reports/render/{id}` | `ApprovalQueue`, `SplitViewReportPreview`, `DigitalSignButton` | Multi-test batch approve, Quick-return for re-testing |
| `/reporting/designer` | Visual Report Template Builder | `GET /reports/templates`<br>`POST /reports/templates/create`<br>`POST /reports/templates/{id}/preview` | `BlockCanvas`, `BlockPalette`, `StyleInspector`, `LivePdfPreviewModal` | Drag reorder, A4 page boundary preview, Normal vs Panic sample data |
| `/reporting/release` | Report Release & Dispatch | `POST /reports/render/{id}`<br>`POST /reports/{id}/deliver` | `ReportTable`, `PdfViewer`, `PrintButton`, `WhatsAppModal` | Draft watermark, Verified sign-off, Delivery audit status |
| `/billing/invoices` | Billing & Cashier Desk | `GET /billing/invoices`<br>`POST /billing/invoices/create`<br>`POST /billing/payments` | `InvoiceTable`, `QuickPaymentModal`, `ThermalReceiptModal` | Split payment (Cash/UPI), Discount authorization, Refund slip |
| `/billing/referrals` | Referral Partner Ledger | `GET /billing/referrals/partners`<br>`GET /billing/referrals/commissions` | `PartnerTable`, `CommissionSummaryCard`, `SettlementModal` | Percentage vs slab rates, Settlement confirmation |
| `/blood_bank/donors` | Blood Donor Registry | `GET /blood_bank/donors`<br>`POST /blood_bank/donors/register`<br>`POST /blood_bank/donations` | `DonorTable`, `ScreeningForm`, `DeferralAlert` | Permanent vs temporary deferral, Donation interval check |
| `/blood_bank/inventory` | Component Inventory & Quarantine | `GET /blood_bank/inventory`<br>`POST /blood_bank/units/{id}/test`<br>`POST /blood_bank/units/{id}/release` | `UnitStockGrid`, `TTIStatusBadge`, `QuarantineReleaseModal` | Expiry warning, Reactive TTI quarantine, Compatible units |
| `/blood_bank/crossmatch`| Compatibility & Unit Issue | `POST /blood_bank/crossmatch`<br>`POST /blood_bank/crossmatch/{id}/approve`<br>`POST /blood_bank/units/{id}/issue` | `CrossMatchWorkflow`, `PatientBloodGroupCard`, `IssueSignOffModal` | Incompatible cross-match block, Transfusion tag print |
| `/admin/users` | User Scopes & Roles | `GET /meta/users`<br>`GET /meta/roles`<br>`POST /meta/users` | `UserTable`, `RoleAssignmentModal`, `BranchScopeSelector` | Active/Inactive toggles, Superadmin badge, Multi-branch scope |
| `/admin/licensing` | Local Server & License Admin | `GET /licensing/status`<br>`POST /licensing/activate`<br>`POST /backup/create` | `LicenseCard`, `MachineFingerprintBox`, `BackupProgress` | License valid/expired, Offline activation file upload, Backup restore |

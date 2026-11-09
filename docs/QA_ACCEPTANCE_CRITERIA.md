# QA Acceptance Criteria & Automated Test Matrix - Aarozi Healthcare

**Author**: QA Automation Lead & Clinical Systems Quality Architect  
**Scope**: Definitive quality gates, automated test matrices, boundary condition validations, and offline acceptance criteria.

---

## 1. Automated Test Suites & Regression Gates

The repository enforces automated verification across backend, frontend, database, and offline interfaces:

```
Total Test Suites Target: 85+ suites
Minimum Test Pass Threshold: 100% Passing (0 failures, 0 regressions)
```

| Suite Name | Scope & Target Files | Key Acceptance Verifications |
| :--- | :--- | :--- |
| **Backend Clinical Routers** | `apps/api/tests/test_clinical_routers.py` | Validates HTTP 200/201 response schemas, request validation, and RBAC permissions across Patients, Pathology, Billing, Blood Bank, and Reports. |
| **Patient Registration & Merge** | `test_patient_model.py`<br>`test_patient_duplicates.py`<br>`test_patient_merge.py` | Verifies soundex duplicate scoring, UHID sequence uniqueness, and financial/clinical entity re-parenting during patient merge. |
| **Pathology Workflow & Worklists** | `test_test_master.py`<br>`test_order_workflow.py`<br>`test_sample_workflow.py`<br>`test_worklists.py` | Order status state machine (`draft` -> `confirmed` -> `in_progress` -> `completed`), accession barcode generation, sample rejection reasons. |
| **Results, Flags & Delta Engine** | `test_reference_ranges.py`<br>`test_result_value_model.py`<br>`test_abnormal_critical_engine.py` | Boundary value evaluation ($[\text{low}, \text{high}]$, $[\text{crit\_low}, \text{crit\_high}]$), automatic `LL`/`HH` alert logging, delta shifts. |
| **Report Engine & Templates** | `test_template_schema.py`<br>`test_template_library.py`<br>`test_renderer.py`<br>`test_digital_signature.py` | JSON schema validation, synthetic data rendering, QR code hash verification, multi-page continuation headers. |
| **Billing & Payments** | `test_price_lists.py`<br>`test_invoice_engine.py`<br>`test_discount_engine.py`<br>`test_refunds_and_cancellation.py` | Multi-item price calculation, discount ceiling enforcement, split payments (Cash/UPI), refund balance tracking. |
| **Referrals & Commissions** | `test_referral_partners.py`<br>`test_commission_ledger.py` | Percentage and slab-based commission accrual, settlement ledger integrity, audit history. |
| **Blood Bank Safety Lifecycle** | `test_donor_master.py`<br>`test_screening.py`<br>`test_donation.py`<br>`test_blood_inventory.py`<br>`test_quarantine_release.py`<br>`test_transfusion.py` | Mandatory TTI screening (HIV, HBV, HCV, Syphilis, Malaria), quarantine lock preventing unreleased unit cross-match, transfusion sign-off. |
| **Offline LAN & Licensing** | `test_license_engine.py`<br>`test_offline_activation.py`<br>`test_backup_restore.py` | Ed25519 signature verification, clock-tamper detection, SQLite fallback, multi-PC LAN source of truth. |
| **RBAC & Multi-Tenant Isolation** | `test_tenant_isolation.py`<br>`test_authorization_engine.py`<br>`test_rbac_e2e.py` | Cross-tenant database access attempts strictly return HTTP 403 Forbidden. |
| **Frontend Type-Check & Lint** | `apps/web: npm run typecheck`<br>`npm run lint` | Strict TypeScript mode (`vue-tsc --noEmit`), zero any-type leaks in clinical components. |

---

## 2. Clinical Data Quality & Boundary Verification Criteria

1. **Age and Sex Stratified Reference Ranges**:
   - Boundary tests verifying neonate ($0-30$ days), infant ($1-12$ months), child ($1-12$ years), adult ($12-60$ years), and geriatric ($>60$ years) intervals.
   - Verified that male and female specific ranges (e.g., Hemoglobin, Serum Ferritin, Uric Acid) apply strictly to the matching patient sex.
2. **Critical Value Escalation Verification**:
   - Potassium result of $2.5 \text{ mEq/L}$ ($< 2.8$) MUST trigger:
     - `flag: "LL"`
     - Insertion into `critical_alerts`
     - Visual red flashing alert on laboratory workstation
     - Mandatory pathologist acknowledgment before report release
3. **Decimal Precision & Rounding**:
   - Serum Creatinine configured with precision 2: `1.054` rounds strictly to `1.05`, and `1.056` rounds strictly to `1.06`.
   - Trailing zeros preserved for clinical significance (e.g., `1.20 mg/dL`).

---

## 3. Report Reproducibility & Historical Integrity Criteria

1. **Immutable Template Versioning**:
   - Release Report $R_1$ using Template $T_1$ (Version 1).
   - Update Template $T$ to Version 2 (change fonts, rearrange columns, alter laboratory address).
   - Re-render Report $R_1$: MUST render identically to original release using Template $T_1$ (Version 1).
2. **Clinical Amendment Trail**:
   - An amended report MUST generate Report Version 2.
   - Report Version 1 MUST be retained with status `amended` and watermark `SUPERSEDED BY REV 2`.
   - The amended report MUST display:
     - Prominent amendment header
     - Clinical reason for amendment
     - Name of amending pathologist and timestamp

---

## 4. Offline LAN Acceptance Criteria

1. **Physical Network Disconnect Test**:
   - Disconnect the local server from the internet (WAN unplugged).
   - Verify that all core laboratory operations succeed with zero errors:
     - Patient Registration & Search
     - Order Accessioning & Barcode Generation
     - Sample Collection & Reception
     - Result Entry & Critical Flagging
     - Pathologist Verification & Report Release
     - Local A4 PDF Rendering & Printing
     - Cashier Invoicing & Receipt Printing
     - Blood Donor Intake & Cross-matching
2. **Multi-PC LAN Concurrency**:
   - 5 client PCs simultaneously querying and entering results against the single authoritative local server.
   - Verified zero lock timeouts, zero dirty reads, and strict sequential accession numbering.

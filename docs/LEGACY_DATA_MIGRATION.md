# Legacy LIS Data Migration & Vice-Versa Export Engine

**Project:** Aarozi Healthcare  
**Module:** Universal Data Importer & Exporter  
**Format Support:** CSV, Excel (.xlsx/.xls), JSON, Portable SQLite  

---

## 1. Migration Challenge & Requirements

When converting an existing diagnostic laboratory from a legacy or competitor LIS (e.g., CrelioHealth, Attune, SoftLab, custom Microsoft Access systems), laboratory owners require:
1. Zero loss of historical patient records, doctor referral directories, and catalog tests.
2. Intelligent handling of varied column headers (e.g. `Patient_Name`, `Full Name`, `PtName`, `Mobile`, `Contact`, `Phone_No`).
3. Pre-flight dry run validation to catch errors before modifying the database.
4. Total reversibility: atomic transactions that roll back if errors exceed the error tolerance threshold.
5. Freedom from vendor lock-in: complete vice-versa export of all Aarozi clinical records at any time.

---

## 2. 3-Step Migration Wizard (`/admin/migration`)

```
+-----------------------------------------------------------------------------------+
|  STEP 1: UPLOAD & AUTO-MAP                                                        |
|  Upload legacy CSV/Excel file -> Machine auto-detects column headers               |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|  STEP 2: PRE-FLIGHT DRY RUN                                                       |
|  Simulates import -> Identifies duplicates -> Computes validation error score     |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|  STEP 3: ATOMIC EXECUTION & ROLLBACK PROTECTION                                   |
|  Transactional commit with automatic safety snapshot & instant rollback on error |
+-----------------------------------------------------------------------------------+
```

---

## 3. Auto-Header Fuzzy Matching Engine

The importer automatically matches messy legacy column names using canonical alias dictionaries:

| Canonical Target | Recognized Legacy Header Variants |
| :--- | :--- |
| `full_name` | `name`, `patient_name`, `patient name`, `pt_name`, `client_name`, `customer` |
| `phone` | `mobile`, `contact`, `phone_number`, `phone_no`, `cell`, `whatsapp` |
| `age` | `age_years`, `yrs`, `patient_age`, `years` |
| `gender` | `sex`, `gender_code`, `m/f` |
| `uhid` | `mrn`, `patient_id`, `reg_no`, `cr_number`, `uhid_no`, `id` |
| `address` | `city`, `location`, `residence`, `area` |

---

## 4. Pre-Flight Dry Run Validation

Before touching the database, the dry-run engine validates every record against business invariants:
- **Phone Number Normalization:** Strips +91, spaces, hyphens; validates 10-digit Indian mobile format.
- **Duplicate Detection:** Flags rows where UHID or phone already exists in the active database or earlier in the file.
- **Gender Normalization:** Converts `M`, `Male`, `m` -> `MALE`; `F`, `Female`, `f` -> `FEMALE`.
- **Validation Report:** Outputs `{ total_rows: 500, valid_rows: 485, duplicate_rows: 12, error_rows: 3, sample_preview: [...] }`.

---

## 5. Vice-Versa Export Engine

Aarozi guarantees **Zero Vendor Lock-In**. Laboratory owners can export their entire historical database at any time with one click:
- **Endpoint:** `GET /api/v1/migration/export?format=zip`
- **Output:** A single compressed `.zip` archive containing:
  - `patients.csv` — Full demographic records, UHIDs, and contact info.
  - `referral_doctors.csv` — Doctor directories, specialties, and commission rates.
  - `test_catalog.csv` — Master test list, sample types, and pricing.
  - `orders_and_results.csv` — Historical test orders, parameters, flags, and values.
  - `aarozi_portable.db` — Clean, portable SQLite database containing all relational tables.


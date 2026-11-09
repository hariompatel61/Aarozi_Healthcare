# Aarozi Healthcare — Legacy LIS Patient Data Migration Guide

---

## 1. Supported Import Formats

The migration engine ([`apps/api/app/services/migration_service.py`](file:///c:/Users/techn/Documents/Aarozi_Healthcare/apps/api/app/services/migration_service.py)) supports bulk historical imports from:
- **CSV / TSV / Tabular Text Files**
- **Excel (.xlsx / .xls) Exports**
- **JSON Structured Dumps**
- **SQLite Database Exports**
- **Aarozi Standard ZIP Packages**

---

## 2. Ingested Data Entities

1. **Patient Master Demographics:** Name, Mobile, Age, Date of Birth, Gender, Address, Email.
2. **Legacy Identifiers:** Legacy MRN, UHID, OPD Number, Old File Number (stored in `patient_identifiers` table).
3. **Doctor Master Records:** Referring Physicians and consultant pathologists.
4. **Test Catalog & Reference Ranges:** Test names, codes, units, normal ranges.
5. **Historical Test Orders & Results:** Verified values tagged with `source_system: MIGRATED_LEGACY_LIS`.

---

## 3. Duplicate Detection & Conflict Strategies

When scanning incoming data, Aarozi checks:
1. Exact match on 10-digit normalized mobile number.
2. Exact match on Legacy MRN / Source Identifier.
3. Fuzzy match on First Name + Age/Sex.

### User-Selectable Strategies:
- **`SKIP_EXISTING` (Recommended):** If a matching patient is found, skips creating a duplicate patient profile.
- **`UPDATE_MISSING`:** Updates blank fields (e.g., adds missing email or address) without overwriting existing clinical notes.
- **`CREATE_NEW`:** Generates a separate patient record with an amended sequence number.

---

## 4. Rollback & Transactional Safety

All imports execute within a database savepoint (`db.begin_nested()`). If a power loss occurs or a malformed row causes an unhandled database exception, the entire batch **rolls back cleanly**, leaving your clinical database 100% uncorrupted.


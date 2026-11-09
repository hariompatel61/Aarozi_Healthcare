# Aarozi Healthcare — Data Export & Inter-Lab Synchronization Guide

---

## 1. Exporting a Complete Clinical Migration Archive

To export your entire laboratory database for backup or migration to another laboratory branch:

1. Open Aarozi Healthcare &rarr; Navigate to **Settings &rarr; Legacy Data Migration**.
2. Click **Export Laboratory ZIP Package** (or call `GET /migration/export`).
3. The server generates:
   `aarozi_migration_package_YYYYMMDD_HHMMSS.zip`
4. The archive contains:
   - `manifest.json`: Metadata, schema version, export timestamp, record counts.
   - `patients.json`: Demographic and contact master records.
   - `test_catalog.json`: Laboratory test investigations, reference ranges, specimen containers.

---

## 2. Importing into Another Authorized Installation

1. On the destination laboratory computer, open the Migration Wizard (`/admin/migration`).
2. Select **Aarozi Migration Package** as the data source.
3. Select your `.zip` archive.
4. Choose your duplicate conflict policy (`SKIP_EXISTING` or `UPDATE_MISSING`).
5. Click **Execute Transactional Import**.
6. The destination server imports all records with transactional integrity, writing full audit trails.


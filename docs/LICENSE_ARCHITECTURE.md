# Aarozi Healthcare — Cryptographic License Architecture

---

## 1. Principles of Offline Licensing

1. **Zero Internet Dependency:** The software must validate commercial rights 100% locally using asymmetric cryptography.
2. **Asymmetric Key Isolation:**
   - **Vendor Private Key (`Ed25519`):** Kept strictly in vendor production secret vaults (`tools/generate_license.js` or secure HSM). Never shipped inside client software or committed to Git.
   - **Vendor Public Key (`Ed25519`):** Registered inside `apps/api/app/licensing/signing.py` (`DEFAULT_ROOT_PUBLIC_KEY_HEX`). Safe to distribute.
3. **One License = One Laboratory Master Server:**
   - A single license authorizes the local master PC that hosts the database.
   - All client computers connecting via LAN (`http://192.168.1.50:8000`) share this master authorization.
   - Unauthorized copying of the license file to an unrelated laboratory is blocked via composite hardware fingerprinting.

---

## 2. Canonical Payload & Signing Structure

To guarantee tamper resistance across different JSON formatting and whitespace, licenses are canonicalized prior to signing:
`canonicalize_license_payload(license_data)` dumps all payload keys sorted alphabetically with no whitespace:

```json
{
  "algorithm": "Ed25519",
  "entitlements": {
    "analyzer_interfacing": true,
    "blood_bank": true,
    "cashier_billing": true,
    "clinical_biochemistry": true,
    "hematology": true,
    "offline_backups": true,
    "pathology": true,
    "template_studio": true,
    "whatsapp_dispatch": true
  },
  "grace_until": "2027-12-09T11:36:04.916Z",
  "installation_id": "HW-89F4-A012-78BC",
  "issued_at": "2026-11-09T11:36:04.916Z",
  "lab_name": "Central Pathology & Diagnostic Center",
  "license_id": "LIC-1794224164916-5121",
  "license_version": 1,
  "limits": {
    "daily_sample_cap": 999999,
    "max_users": 45,
    "max_workstations": 15
  },
  "mode": "OFFLINE_LOCAL",
  "plan_code": "COMMERCIAL_PRO",
  "signing_key_id": "aarozi-root-key-2026",
  "tenant_id": "11111111-1111-1111-1111-111111111111",
  "valid_from": "2026-11-08T11:36:04.916Z",
  "valid_to": "2027-11-09T11:36:04.916Z",
  "signature": "353bc5669a736869b1e3105eb171ab83e2ad03c9df0049366102be6085b3426ec421638e4301803d4268405bb16dc87d32241e8da75cae5f94550f8afcaf5c02"
}
```

---

## 3. Tamper & Exploitation Protections

### A. Clock Rollback Protection
If an operator changes the system time back to 2020:
The application tracks `last_trusted_time` on every patient registration and transaction. If `current_system_time < last_trusted_time`, the system detects clock rollback, revokes the active session to `REVOKED_CLOCK_ROLLBACK`, and writes an immutable audit record.

### B. Hardware Cloning Detection
The license binds to:
`SHA256(Motherboard_UUID + CPU_Processor_ID + Primary_Disk_Serial)`.
If a laboratory clones their Windows disk image onto a second computer, the hardware hash mismatches and the second installation operates in unverified mode.

### C. Zero Medical Data Deletion on Expiration
In strict accordance with healthcare compliance:
When a license reaches expiration + grace period, **no clinical, patient, blood bank, or financial record is deleted or modified**. The system transitions to a clean read-only mode, permitting full search, report viewing, printing, and data export.


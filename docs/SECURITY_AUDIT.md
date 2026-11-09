# Security Architecture, Threat Model & Compliance Audit

**Project:** Aarozi Healthcare  
**Scope:** Offline-First Clinical LIS Security  
**Standards Alignment:** India DISHA, ISO 27001, HIPAA Security Rule, NABL ISO 15189 Technical Controls  

---

## 1. Threat Model & Trust Boundaries

```
[ UNTRUSTED ZONE: Public Internet ]
      |
      | (TLS 1.3 / HTTPS Only)
      v
+-----------------------------------------------------------------+
| CENTRAL PLATFORM BOUNDARY                                       |
| - Handles only payments, user accounts, and license issuance    |
| - STRICT POLICY: Zero patient clinical or financial records     |
+-----------------------------------------------------------------+
      |
      | (Signed .lic file via out-of-band download or email)
      v
+=================================================================+
| TRUSTED LOCAL ZONE: Diagnostic Laboratory Physical LAN          |
|                                                                 |
| [Laboratory Master PC]                                          |
| - Sole authority for clinical records                           |
| - SQLite WAL mode with foreign key integrity                    |
| - Direct OAuth to customer Google account (no intermediary)     |
|                                                                 |
| [Workstation Browsers]                                          |
| - Restricted to Local Subnet (192.168.x.x / 10.x.x.x)           |
| - Scoped RBAC tokens (Pathologist, Reception, Technician)       |
+=================================================================+
```

---

## 2. Zero-Trust Security Invariants

1. **Server-Derived Context (Rule #7):**
   - The server never trusts `tenant_id`, `user_id`, or `patient_id` supplied by the browser request body or query parameters when the authenticated session context can derive it.
   - Any attempt to access data outside the tenant or user boundary yields an immediate HTTP 403 Forbidden.
2. **Zero Plaintext Credentials:**
   - User passwords are protected using PBKDF2 with SHA-256 and unique per-user cryptographic salts (`passlib`).
   - Offline license signing uses Ed25519 asymmetric cryptography; private keys are never included in distributed client software.
3. **No Patient Payload Logging (Rule #8):**
   - Production server logging (`run_server.py`) explicitly suppresses raw HTTP request payloads containing patient demographics, test results, or diagnostic observations.
4. **Local Token Vault Isolation:**
   - Google OAuth access and refresh tokens are encrypted and retained strictly in the local database on the Master PC. They are never synchronized to vendor servers.

---

## 3. Clock Rollback & Anti-Tampering Engine

To prevent malicious system clock manipulation aimed at indefinitely extending expired licenses:
- Aarozi records a high-water mark timestamp on every clinical write (patient intake, test result entry, invoice creation).
- On application boot and during every transaction check, the current wall-clock time is compared against the database high-water mark.
- If `current_system_time < last_recorded_transaction_time`, the system detects an intentional clock rollback and transitions to an integrity verification lock until administrative review.

---

## 4. Compliance & Audit Logging

- **Audit Trails:** All modifications to clinical results, sample statuses, and financial receipts create immutable audit trail records (`created_by`, `timestamp`, `old_value`, `new_value`, `reason`).
- **NABL (ISO 15189) Alignment:** Calibration logs, quality control rules (Westgard rules), and instrument serial logs are permanently preserved and cannot be overwritten.


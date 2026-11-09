# Aarozi Healthcare — Healthcare Security, DPDP Act & Hardening Guide

---

## 1. Compliance with Indian Digital Personal Data Protection (DPDP) Act 2023

1. **Purpose Limitation:** Patient health data (demographics, test results, diagnoses) is collected strictly for diagnostic reporting and clinical treatment.
2. **Data Minimization:** No personal health information (PHI) is transmitted off-premises in offline mode. License activation and renewal request payloads contain only hardware hashes, license nonces, and tenant identifiers — zero patient payloads.
3. **Local Encryption at Rest:** SQLite databases can be protected via SQLCipher or BitLocker drive encryption on Windows 10/11 Pro.
4. **Encryption in Transit:** All local and cloud API endpoints communicate over HTTPS (TLS 1.3) with automated certificates via Caddy.

---

## 2. Access Control & RBAC Matrix

| Role | Patient Reg (F2) | Result Entry | Doctor Sign-Off | Billing & Cashier | License Admin |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Receptionist** | Full | None | None | Full | None |
| **Lab Technician** | View | Full | Draft | View | None |
| **Consultant Pathologist** | View | Full | **Full Sign-Off** | View | None |
| **Cashier** | None | None | None | **Full Billing** | None |
| **Lab Director / Admin** | Full | Full | Full | Full | **Full Access** |

---

## 3. Tamper-Proof Audit Logging

Every critical event is logged with an immutable audit event:
- User login / logout / failed login.
- Specimen barcode generation.
- Test result entry, verification, and amendment.
- Report delivery (WhatsApp / PDF print).
- License import, renewal, and clock rollback detection.
- Database backup creation and restore.

Audit records are append-only and cannot be altered through standard UI workflows.


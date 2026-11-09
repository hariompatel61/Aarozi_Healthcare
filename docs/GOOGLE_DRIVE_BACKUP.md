# Aarozi Healthcare — Google Drive Customer Backup Guide

---

## 1. Overview & Architecture

Every laboratory owner can connect their own Google account directly from the local Aarozi settings.

```
[ Master Lab PC ]
       │
       ▼ (1. Hot Crash-Consistent Backup via SQLite Online Backup API)
[ dev_aarozi_snapshot.db ]
       │
       ▼ (2. Client-Side AES-256 Encryption with Lab Private Key)
[ aarozi_backup_20261109.db.enc ]
       │
       ▼ (3. Direct HTTPS Upload via Google Drive v3 REST API)
[ Customer's Own Google Drive / "Aarozi Healthcare Backups" ]
```

---

## 2. Least-Privilege OAuth 2.0 Scope

Aarozi Healthcare requests strictly:
`https://www.googleapis.com/auth/drive.file`

### Security Guarantees:
- **Zero Visibility into Customer Personal Files:** Aarozi cannot read or list personal photos, documents, or spreadsheets in the customer's Google Drive.
- **Isolated App Folder:** Aarozi only accesses the `Aarozi Healthcare Backups` folder it creates.
- **Revocable at Any Time:** The customer can revoke access in one click from Aarozi settings or directly in their [Google Account Security Settings](https://myaccount.google.com/permissions).

---

## 3. Step-by-Step Laboratory Setup

1. Open Aarozi Healthcare in Google Chrome (`http://localhost:8000`).
2. Navigate to **Settings &rarr; System Licensing**.
3. Under **Customer-Owned Google Drive Cloud Vault**, click **Connect Google Drive**.
4. Log in to your clinic's Google account and grant permission.
5. Once connected, your email address is displayed.
6. Click **Sync to Google Drive** to perform your first automated backup!


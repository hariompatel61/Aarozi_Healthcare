# Google Drive Backup & Disaster Recovery Architecture

**Project:** Aarozi Healthcare  
**Scope:** Customer-Owned Cloud Vault Integration  
**OAuth Scope:** `https://www.googleapis.com/auth/drive.file` (Least-Privilege: Access only to files created by Aarozi)  

---

## 1. Zero Vendor Storage Principle

Aarozi Healthcare explicitly rejects the traditional multi-tenant SaaS hosting model where the software vendor pays high recurring cloud fees to store gigabytes of medical reports, scanned prescriptions, and SQL databases for 10,000+ laboratories.

Under this architecture:
- Each laboratory owner connects their **own Google Account** (personal Gmail or Google Workspace).
- Backups consume the lab owner's 15 GB free tier or expanded Google One/Workspace storage.
- The Aarozi vendor server **never sees, touches, or routes** the laboratory's database backups.

---

## 2. Google OAuth 2.0 Flow & Token Security

1. **Authorization Request:**
   - User navigates to **Admin -> Licensing & Cloud Vault -> Connect Google Drive**.
   - Local server generates Google OAuth 2.0 authorization URL with `access_type=offline`, `prompt=consent`, and `scope=drive.file`.
2. **Callback Handling:**
   - Google redirects to `/api/v1/integrations/google-drive/callback` on the local server.
   - Local server exchanges authorization code for `access_token` and `refresh_token`.
3. **Local Token Vault:**
   - Tokens are stored locally in the lab's `local_vault_tokens` table on the Master PC.
   - Tokens are encrypted at rest and never shared with central vendor servers.
4. **Token Refresh:**
   - Before any scheduled backup, the local service checks token expiry and automatically uses the refresh token to acquire a fresh access token directly from Google.

---

## 3. Hot SQLite Backup Engine

To avoid database locking errors while active diagnostic testing or invoicing is occurring:
- Standard file copy (`shutil.copy2`) is prohibited during live execution because SQLite in WAL mode can produce corrupted snapshots.
- Aarozi uses the **SQLite Online Backup API** (`sqlite3.Connection.backup` or `VACUUM INTO`):

```python
def create_hot_sqlite_snapshot(source_db_path: Path, output_snapshot_path: Path) -> str:
    src_conn = sqlite3.connect(str(source_db_path))
    dest_conn = sqlite3.connect(str(output_snapshot_path))
    with dest_conn:
        src_conn.backup(dest_conn, pages=100)
    dest_conn.close()
    src_conn.close()

    # Compute SHA-256 Checksum
    hasher = hashlib.sha256()
    with open(output_snapshot_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()
```

---

## 4. Google Drive Direct Upload

The Master PC uploads the hot snapshot directly to the Google Drive API (`https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart`):
- Creates a dedicated folder: `Aarozi_Healthcare_Backups/`
- Uploads the database snapshot: `aarozi_backup_YYYYMMDD_HHMMSS.db`
- Attaches the SHA-256 integrity hash as Drive file description and custom properties.
- Prunes remote backups older than the lab's retention policy (default: 30 days).

---

## 5. Local & Disaster Recovery Utilities

### Automated Local Backup (`scripts/backup_database.py`)
Can be executed as a scheduled Windows Task:
```cmd
python scripts\backup_database.py --retention-days 30 --out-dir ./backups
```

### Verified Database Restore (`scripts/restore_database.py`)
In the event of hardware failure, disk corruption, or accidental data loss:
1. Validates the SHA-256 checksum against `.sha256` digest file.
2. Automatically creates a safety snapshot of the active live database before replacing it (`dev_aarozi_pre_restore_YYYYMMDD_HHMMSS.db`).
3. Restores the verified backup cleanly.
```cmd
python scripts\restore_database.py --backup ./backups/aarozi_backup_20261109_120000.db
```


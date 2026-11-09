# Aarozi Healthcare — Backup & Disaster Recovery Guide

---

## 1. Local Automated Backup Architecture

Aarozi Healthcare implements the SQLite Online Backup API to generate crash-consistent, non-locking hot snapshots of `dev_aarozi.db` while clinical operations continue in real-time.

### Backup Schedule
- **Automated Daily Snapshot:** Every night at 02:00 AM.
- **Pre-Update Snapshot:** Automatically executed before any software version patch.
- **On-Demand Snapshot:** Triggerable from **Settings &rarr; System Licensing &rarr; Create Snapshot**.

---

## 2. Integrity Verification (SHA-256)

Every generated backup file:
`aarozi_backup_YYYYMMDD_HHMMSS.db`
is accompanied by its cryptographic digest:
`aarozi_backup_YYYYMMDD_HHMMSS.db.sha256`

The restore engine automatically verifies that the digest matches before allowing any database overwrite, preventing corrupted restores caused by failing hard drives or power cuts.

---

## 3. Running Automated Backups via Windows Task Scheduler

To schedule daily midnight backups on the Master PC:
1. Open Windows **Task Scheduler**.
2. Click **Create Basic Task** &rarr; Name: `Aarozi Daily Database Backup`.
3. Trigger: **Daily at 02:00 AM**.
4. Action: **Start a program**:
   - Program: `python` (or bundled runner)
   - Arguments: `scripts\backup_database.py --retention-days 30 --out-dir D:\AaroziBackups`
5. Click **Finish**.

---

## 4. Disaster Recovery (Server PC Hardware Failure)

When a master PC hardware failure occurs (burned motherboard or drive crash):
1. **Prepare New Computer:** Connect new PC to lab network and set IP to `192.168.1.50`.
2. **Install Clean Aarozi:** Run `AaroziHealthcare-Setup-v1.0.0.exe`.
3. **Restore Database:**
   ```cmd
   python scripts\restore_database.py --backup D:\AaroziBackups\aarozi_backup_latest.db
   ```
4. **Reactivate License:** In Customer Portal (`/customer/dashboard`), submit a **Hardware Migration Request** with the new PC's hardware fingerprint, download the updated `.lic` file, and import it into the local server.
5. All patient records, billing ledgers, and analyzer configurations are restored!


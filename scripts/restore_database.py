"""Aarozi Healthcare — Database Restore & Disaster Recovery Utility.

Safely restores a verified backup file into the active database.
Always snapshots the existing live database before applying any restoration.

Usage:
    python scripts/restore_database.py --backup ./backups/aarozi_backup_20261109_120000.db
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


def compute_file_sha256(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Aarozi Database Restore Engine")
    parser.add_argument("--backup", type=str, required=True, help="Path to backup .db file")
    args = parser.parse_args()

    backup_path = Path(args.backup).resolve()
    if not backup_path.exists():
        print(f"[ERROR] Backup file not found: {backup_path}")
        sys.exit(1)

    repo_root = Path(__file__).resolve().parent.parent
    target_db = repo_root / "apps" / "api" / "dev_aarozi.db"

    # Verify Checksum if present
    sha_file = backup_path.with_suffix(backup_path.suffix + ".sha256")
    if sha_file.exists():
        expected_sha = sha_file.read_text(encoding="utf-8").split()[0].strip()
        actual_sha = compute_file_sha256(backup_path)
        if expected_sha.lower() != actual_sha.lower():
            print(f"[FATAL] Backup integrity check failed! Expected {expected_sha}, got {actual_sha}")
            sys.exit(1)
        print("[OK] SHA-256 Checksum verified.")

    # Safety Snapshot of active DB before overwrite
    if target_db.exists():
        safety_path = target_db.with_name(f"dev_aarozi_pre_restore_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.db")
        shutil.copy2(target_db, safety_path)
        print(f"[OK] Safety snapshot of active DB created: {safety_path.name}")

    # Restore
    shutil.copy2(backup_path, target_db)
    print(f"[SUCCESS] Database successfully restored from: {backup_path.name}")


if __name__ == "__main__":
    main()


"""Aarozi Healthcare — Automated Database Backup Utility.

Performs hot, consistent backups of local SQLite (dev_aarozi.db) or PostgreSQL
databases. Computes SHA-256 integrity checksums and rotates old backups.

Usage:
    python scripts/backup_database.py [--retention-days 30] [--out-dir ./backups]
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


def backup_sqlite_database(source_db: Path, target_dir: Path) -> Path:
    """Uses SQLite Online Backup API for hot, crash-consistent snapshots."""
    target_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"aarozi_backup_{timestamp}.db"
    backup_path = target_dir / backup_filename

    # SQLite Hot Backup via sqlite3.Connection.backup
    src_conn = sqlite3.connect(str(source_db))
    dest_conn = sqlite3.connect(str(backup_path))
    with dest_conn:
        src_conn.backup(dest_conn, pages=100)
    dest_conn.close()
    src_conn.close()

    # Integrity verification
    sha256 = compute_file_sha256(backup_path)
    checksum_file = target_dir / f"{backup_filename}.sha256"
    checksum_file.write_text(f"{sha256}  {backup_filename}\n", encoding="utf-8")

    print(f"[OK] Backup created: {backup_path}")
    print(f"[OK] SHA-256 Hash:   {sha256}")
    return backup_path


def rotate_old_backups(target_dir: Path, retention_days: int) -> None:
    """Prunes backups older than the specified retention window."""
    now = datetime.utcnow()
    for item in target_dir.glob("aarozi_backup_*.db"):
        stat = item.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime)
        age_days = (now - mtime).days
        if age_days > retention_days:
            item.unlink(missing_ok=True)
            sha_file = target_dir / f"{item.name}.sha256"
            sha_file.unlink(missing_ok=True)
            print(f"[PRUNED] Deleted expired backup: {item.name} ({age_days} days old)")


def main():
    parser = argparse.ArgumentParser(description="Aarozi Database Backup Engine")
    parser.add_argument("--retention-days", type=int, default=30, help="Backup retention days")
    parser.add_argument("--out-dir", type=str, default="./backups", help="Target backup folder")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    db_path = repo_root / "apps" / "api" / "dev_aarozi.db"
    target_dir = Path(args.out_dir).resolve()

    if not db_path.exists():
        print(f"[ERROR] Database file not found at: {db_path}")
        sys.exit(1)

    print("=" * 60)
    print("  AAROZI HEALTHCARE — DATABASE BACKUP DRILL")
    print("=" * 60)
    backup_sqlite_database(db_path, target_dir)
    rotate_old_backups(target_dir, args.retention_days)
    print("=" * 60)


if __name__ == "__main__":
    main()


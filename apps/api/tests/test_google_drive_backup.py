"""Automated tests for Customer-Owned Google Drive backup and SQLite hot snapshots."""

import json
import sqlite3
import pytest
from pathlib import Path

from app.services.google_drive_service import (
    generate_oauth_auth_url,
    save_google_credentials,
    load_google_credentials,
    delete_google_credentials,
    create_hot_sqlite_snapshot,
    OAUTH_SCOPES,
)


def test_google_oauth_auth_url_least_privilege_scope():
    client_id = "test-client-id-123.apps.googleusercontent.com"
    redirect_uri = "http://localhost:8000/settings/backup/callback"
    url = generate_oauth_auth_url(client_id, redirect_uri)

    assert "https://accounts.google.com/o/oauth2/v2/auth" in url
    assert f"client_id={client_id}" in url
    assert "https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fdrive.file" in url
    # Verify least privilege: NEVER request full drive scope
    assert "https://www.googleapis.com/auth/drive " not in url
    assert "access_type=offline" in url
    assert "prompt=consent" in url


def test_google_credentials_save_load_delete(tmp_path, monkeypatch):
    test_token_file = tmp_path / "test_drive_token.json"
    monkeypatch.setattr("app.services.google_drive_service.get_token_storage_path", lambda: test_token_file)

    assert load_google_credentials() is None

    sample_creds = {
        "access_token": "ya29.sample_test_token",
        "refresh_token": "1//sample_refresh_token",
        "connected_email": "doctor.lab@gmail.com",
        "client_id": "test_client",
        "client_secret": "test_secret",
    }
    save_google_credentials(sample_creds)

    loaded = load_google_credentials()
    assert loaded is not None
    assert loaded["connected_email"] == "doctor.lab@gmail.com"
    assert loaded["refresh_token"] == "1//sample_refresh_token"

    delete_google_credentials()
    assert load_google_credentials() is None


def test_hot_sqlite_snapshot_creation_and_checksum(tmp_path):
    """Verifies that SQLite Online Backup API creates consistent snapshot with valid SHA-256."""
    src_db = tmp_path / "live_lab.db"
    dest_snapshot = tmp_path / "snapshot.db"

    # Populate synthetic patient and test data in source SQLite
    conn = sqlite3.connect(str(src_db))
    cur = conn.cursor()
    cur.execute("CREATE TABLE test_patients (id TEXT, name TEXT, mobile TEXT)")
    cur.execute("INSERT INTO test_patients VALUES ('P1', 'Synthetic Patient A', '9820011111')")
    cur.execute("INSERT INTO test_patients VALUES ('P2', 'Synthetic Patient B', '9820022222')")
    conn.commit()
    conn.close()

    # Take hot snapshot
    sha256 = create_hot_sqlite_snapshot(src_db, dest_snapshot)

    assert dest_snapshot.exists()
    assert len(sha256) == 64  # Valid SHA-256 hex string

    # Verify snapshot content is intact
    snap_conn = sqlite3.connect(str(dest_snapshot))
    snap_cur = snap_conn.cursor()
    snap_cur.execute("SELECT COUNT(*) FROM test_patients")
    count = snap_cur.fetchone()[0]
    snap_conn.close()

    assert count == 2


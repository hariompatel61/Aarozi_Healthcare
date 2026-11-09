"""Google Drive Customer-Owned Backup Router."""

from __future__ import annotations

import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.security.auth import get_current_user
from app.models.identity import User
from app.services.google_drive_service import (
    generate_oauth_auth_url,
    exchange_code_for_tokens,
    load_google_credentials,
    revoke_google_connection,
    upload_backup_to_customer_drive,
    list_customer_drive_backups,
)

router = APIRouter(prefix="/google-drive", tags=["google-drive"])


class OAuthCallbackRequest(BaseModel):
    code: str
    redirect_uri: str


@router.get("/auth-url")
def api_get_google_auth_url(redirect_uri: str = "http://localhost:8000/settings/backup/callback"):
    """Generates the Google OAuth 2.0 authorization URL for the laboratory owner."""
    client_id = os.environ.get("GOOGLE_DRIVE_CLIENT_ID", "aarozi-drive-client-id.apps.googleusercontent.com")
    url = generate_oauth_auth_url(client_id, redirect_uri)
    return {"auth_url": url, "client_id": client_id}


@router.post("/callback")
async def api_google_oauth_callback(
    body: OAuthCallbackRequest,
    current_user: User = Depends(get_current_user),
):
    """Exchanges authorization code for customer tokens and stores them locally."""
    client_id = os.environ.get("GOOGLE_DRIVE_CLIENT_ID", "aarozi-drive-client-id.apps.googleusercontent.com")
    client_secret = os.environ.get("GOOGLE_DRIVE_CLIENT_SECRET", "aarozi-secret-test")

    try:
        creds = await exchange_code_for_tokens(client_id, client_secret, body.code, body.redirect_uri)
        return {
            "status": "connected",
            "email": creds.get("connected_email"),
            "connected_at": creds.get("created_at"),
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/status")
def api_get_google_drive_status():
    """Returns the local Google Drive connection state for the lab."""
    creds = load_google_credentials()
    if not creds:
        return {
            "is_connected": False,
            "connected_email": None,
            "storage_provider": "Google Drive (Customer-Owned)",
        }
    return {
        "is_connected": True,
        "connected_email": creds.get("connected_email"),
        "storage_provider": "Google Drive (Customer-Owned)",
        "connected_at": creds.get("created_at"),
    }


@router.post("/backup")
async def api_trigger_google_drive_backup(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Takes hot SQLite snapshot and uploads directly to customer's Google Drive."""
    repo_root = Path(__file__).resolve().parents[3]
    db_path = repo_root / "apps" / "api" / "dev_aarozi.db"

    if not db_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Database file not found.")

    try:
        result = await upload_backup_to_customer_drive(
            source_db_path=db_path,
            organization_id=current_user.tenant_id,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/backups")
async def api_list_google_drive_backups():
    """Lists existing backup snapshots stored in the customer's Google Drive."""
    try:
        backups = await list_customer_drive_backups()
        return {"backups": backups, "count": len(backups)}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/disconnect")
async def api_disconnect_google_drive():
    """Revokes OAuth tokens and disconnects Google Drive."""
    await revoke_google_connection()
    return {"status": "disconnected"}


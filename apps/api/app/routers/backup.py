"""Backup and restore router for Aarozi Healthcare offline local server."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.security.auth import get_current_user
from app.models.identity import User
from app.backup.service import create_local_backup, restore_local_backup


router = APIRouter(prefix="/backup", tags=["backup"])


class BackupRestoreRequest(BaseModel):
    metadata: dict = Field(..., description="Backup metadata including checksum and tenant_id")
    payload: dict = Field(..., description="Backup content payload")


@router.post("/export", status_code=status.HTTP_201_CREATED)
def api_create_backup(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        backup, bundle = create_local_backup(db, current_user.tenant_id, actor_user_id=current_user.id)
        return bundle
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/restore", status_code=status.HTTP_200_OK)
def api_restore_backup(
    body: BackupRestoreRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        bundle = {"metadata": body.metadata, "payload": body.payload}
        result = restore_local_backup(db, current_user.tenant_id, bundle, actor_user_id=current_user.id)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


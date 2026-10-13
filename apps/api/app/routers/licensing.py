"""Offline licensing router."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session

from app.db import get_db
from app.security.auth import get_current_user
from app.models.identity import User
from app.licensing.service import (
    verify_and_update_license_status,
    import_license,
    create_activation_request,
    create_renewal_request,
)

router = APIRouter(prefix="/licensing", tags=["licensing"])


class LicenseImportRequest(BaseModel):
    license_version: int | None = 1
    license_id: str | None = None
    tenant_id: str | None = None
    installation_id: str | None = None
    plan_code: str | None = None
    mode: str = "OFFLINE_LOCAL"
    valid_from: str
    valid_to: str
    grace_until: str | None = None
    entitlements: dict = Field(default_factory=dict)
    limits: dict = Field(default_factory=dict)
    signing_key_id: str | None = None
    algorithm: str | None = None
    signature: str | None = None
    issued_at: str | None = None

    model_config = ConfigDict(extra="allow")


class ActivationRequestInput(BaseModel):
    installation_id: str
    requested_modules: dict = Field(default_factory=dict)
    limits: dict = Field(default_factory=dict)
    requested_mode: str = "OFFLINE_LOCAL"


@router.post("/activation-request", status_code=status.HTTP_201_CREATED)
def api_create_activation_request(
    body: ActivationRequestInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    req = create_activation_request(
        db=db,
        tenant_id=current_user.tenant_id,
        installation_id=body.installation_id,
        requested_modules=body.requested_modules,
        limits=body.limits,
        requested_mode=body.requested_mode,
    )
    return {
        "id": req.id,
        "tenant_id": req.tenant_id,
        "installation_id": req.installation_id,
        "request_nonce": req.request_nonce,
        "request_payload": req.request_payload_json,
        "status": req.status,
    }



class RenewalRequestInput(BaseModel):
    installation_id: str
    requested_modules: dict = Field(default_factory=dict)
    limits: dict = Field(default_factory=dict)


@router.post("/renewal-request", status_code=status.HTTP_201_CREATED)
def api_create_renewal_request(
    body: RenewalRequestInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    req = create_renewal_request(
        db=db,
        tenant_id=current_user.tenant_id,
        installation_id=body.installation_id,
        requested_modules=body.requested_modules,
        limits=body.limits,
    )
    return {
        "id": req.id,
        "tenant_id": req.tenant_id,
        "installation_id": req.installation_id,
        "request_nonce": req.request_nonce,
        "request_payload": req.request_payload_json,
        "status": req.status,
    }



@router.get("/status")
def api_get_license_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    status_res = verify_and_update_license_status(db, current_user.tenant_id)
    return status_res


@router.post("/import", status_code=status.HTTP_201_CREATED)
def api_import_license(
    body: LicenseImportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        lic = import_license(db, current_user.tenant_id, body.model_dump(), user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return {
        "id": lic.id,
        "tenant_id": lic.tenant_id,
        "mode": lic.mode,
        "status": lic.status,
        "valid_to": lic.valid_to.isoformat(),
    }

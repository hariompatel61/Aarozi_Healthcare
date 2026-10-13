"""Patient API router for duplicates detection and merge."""
from __future__ import annotations

from datetime import date
from typing import Any
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.patient.duplicates import (
    detect_duplicates,
    execute_patient_merge,
)
from app.rbac.engine import enforce_permission
from app.security.auth import get_current_user
from app.security.tenant_guard import get_tenant_context, TenantContext

router = APIRouter(prefix="/patients", tags=["patients"])


class DuplicateCheckRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    mobile: str | None = None
    identifier_type: str | None = None
    identifier_value: str | None = None
    date_of_birth: date | None = None
    threshold: float = Field(0.6, ge=0.0, le=1.0)
    limit: int = Field(10, ge=1, le=50)
    exclude_patient_id: str | None = None


class DuplicateMatchResponse(BaseModel):
    patient_id: str
    patient_no: str
    first_name: str
    last_name: str | None = None
    mobile: str | None = None
    date_of_birth: date | None = None
    match_score: float
    reasons: list[str]


class PatientMergeRequest(BaseModel):
    source_patient_id: str
    target_patient_id: str
    reason: str


class PatientMergeResponse(BaseModel):
    audit_id: str
    source_patient_id: str
    target_patient_id: str
    reason: str
    created_at: str
    merge_details: dict[str, Any]


@router.post("/duplicates/check", response_model=list[DuplicateMatchResponse])
def check_patient_duplicates(
    payload: DuplicateCheckRequest,
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_tenant_context),
    current_user: Any = Depends(get_current_user),
) -> list[DuplicateMatchResponse]:
    """Check potential duplicates before registration or during workflow."""
    enforce_permission(db, current_user, "patient.view")

    matches = detect_duplicates(
        db,
        tenant_context=tenant_context,
        first_name=payload.first_name,
        last_name=payload.last_name,
        mobile=payload.mobile,
        identifier_type=payload.identifier_type,
        identifier_value=payload.identifier_value,
        date_of_birth=payload.date_of_birth,
        threshold=payload.threshold,
        limit=payload.limit,
        exclude_patient_id=payload.exclude_patient_id,
    )

    return [
        DuplicateMatchResponse(
            patient_id=m.patient.id,
            patient_no=m.patient.patient_no,
            first_name=m.patient.first_name,
            last_name=m.patient.last_name,
            mobile=m.patient.mobile_normalized,
            date_of_birth=m.patient.date_of_birth,
            match_score=m.match_score,
            reasons=m.reasons,
        )
        for m in matches
    ]


@router.post("/merge", response_model=PatientMergeResponse, status_code=status.HTTP_200_OK)
def merge_patients(
    payload: PatientMergeRequest,
    db: Session = Depends(get_db),
    tenant_context: TenantContext = Depends(get_tenant_context),
    current_user: Any = Depends(get_current_user),
) -> PatientMergeResponse:
    """Execute a controlled patient merge with authorization and durable audit."""
    enforce_permission(db, current_user, "patient.merge")

    merge_audit = execute_patient_merge(
        db,
        tenant_context=tenant_context,
        source_patient_id=payload.source_patient_id,
        target_patient_id=payload.target_patient_id,
        reason=payload.reason,
        actor_user_id=getattr(current_user, "id", None),
    )
    db.commit()

    return PatientMergeResponse(
        audit_id=merge_audit.id,
        source_patient_id=merge_audit.source_patient_id,
        target_patient_id=merge_audit.target_patient_id,
        reason=merge_audit.reason,
        created_at=merge_audit.created_at.isoformat() if merge_audit.created_at else "",
        merge_details=merge_audit.merge_details_json,
    )

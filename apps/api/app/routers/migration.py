"""Patient Data Migration and Cross-Laboratory Ingestion Router."""

from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, File, Form, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.security.auth import get_current_user
from app.models.identity import User
from app.services.migration_service import (
    parse_csv_content,
    auto_map_headers,
    detect_patient_duplicates,
    execute_patient_migration,
    export_complete_migration_package,
)

router = APIRouter(prefix="/migration", tags=["migration"])


class MigrationPreviewRequest(BaseModel):
    csv_content: str | None = None
    json_records: list[dict] | None = None
    source_name: str = "LEGACY_LIS"


class MigrationExecuteRequest(BaseModel):
    records: list[dict]
    field_mapping: dict[str, str]
    conflict_strategy: str = "SKIP_EXISTING"  # SKIP_EXISTING | UPDATE_MISSING | CREATE_NEW
    source_name: str = "LEGACY_LIS"


@router.post("/preview")
def api_preview_migration(
    body: MigrationPreviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Parses legacy data, auto-maps columns, and identifies duplicates before importing.
    """
    records = []
    if body.csv_content:
        records = parse_csv_content(body.csv_content)
    elif body.json_records:
        records = body.json_records
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No data content provided.")

    if not records:
        return {"headers": [], "total_records": 0, "preview_rows": [], "duplicates_found": 0}

    headers = list(records[0].keys())
    mapping = auto_map_headers(headers)

    # Perform duplicate check on first 50 records for instant preview
    mapped_sample = []
    for r in records[:50]:
        item = {mapping[k]: v for k, v in r.items() if k in mapping and mapping[k]}
        mapped_sample.append(item)

    duplicate_analysis = detect_patient_duplicates(db, current_user.tenant_id, mapped_sample)
    dup_count = sum(1 for d in duplicate_analysis if d["is_duplicate"])

    return {
        "headers": headers,
        "auto_mapping": mapping,
        "total_records": len(records),
        "preview_sample_count": len(mapped_sample),
        "duplicates_in_sample": dup_count,
        "sample_preview": duplicate_analysis[:10],
    }


@router.post("/execute", status_code=status.HTTP_201_CREATED)
def api_execute_migration(
    body: MigrationExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Executes safe transactional import with automatic rollback on error."""
    try:
        summary = execute_patient_migration(
            db=db,
            tenant_id=current_user.tenant_id,
            raw_records=body.records,
            field_mapping=body.field_mapping,
            conflict_strategy=body.conflict_strategy,
            source_name=body.source_name,
            actor_user_id=current_user.id,
        )
        return summary
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/export")
def api_export_migration_package(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Exports entire laboratory clinical dataset into an offline portable ZIP archive."""
    try:
        zip_bytes = export_complete_migration_package(db, current_user.tenant_id)
        filename = f"aarozi_migration_package_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip"
        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


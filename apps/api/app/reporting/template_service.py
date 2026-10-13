"""Report Template Service: JSON Schema validation, template primitives, and immutable versioning."""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

import jsonschema
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.orm import Session

from app.audit.service import log_audit_event
from app.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.identity import User
from app.models.reporting import ReportTemplate
from app.rbac.engine import authorize_action
from app.security.tenant_guard import TenantContext, verify_tenant_boundary


_SCHEMA_FILE = Path(__file__).resolve().parents[4] / "contracts" / "report-template.schema.json"
_CACHED_SCHEMA: dict[str, Any] | None = None


def get_json_schema() -> dict[str, Any]:
    global _CACHED_SCHEMA
    if _CACHED_SCHEMA is None:
        if not _SCHEMA_FILE.is_file():
            raise FileNotFoundError(f"Report template schema file '{_SCHEMA_FILE}' not found")
        _CACHED_SCHEMA = json.loads(_SCHEMA_FILE.read_text(encoding="utf-8"))
    return _CACHED_SCHEMA


def validate_template_schema(template_dict: dict[str, Any]) -> None:
    schema = get_json_schema()
    try:
        jsonschema.validate(instance=template_dict, schema=schema)
    except jsonschema.ValidationError as err:
        path_str = ".".join(str(p) for p in err.path) if err.path else "root"
        raise ValidationError(f"Invalid report template schema at '{path_str}': {err.message}", field=path_str)


def _check_template_permission(
    db: Session,
    *,
    tenant_context: TenantContext,
    actor_user_id: str | None = None,
) -> None:
    user_id = actor_user_id or tenant_context.user_id
    if not user_id:
        return
    user = db.query(User).filter(User.id == user_id, User.tenant_id == tenant_context.tenant_id).first()
    if user and not (
        authorize_action(db, user, "report.template.manage", branch_id=tenant_context.branch_id)
        or authorize_action(db, user, "report.release", branch_id=tenant_context.branch_id)
        or authorize_action(db, user, "report.view", branch_id=tenant_context.branch_id)
    ):
        raise ForbiddenError("User is not authorized to manage report templates")


def create_report_template(
    db: Session,
    *,
    tenant_context: TenantContext,
    code: str,
    name: str,
    category: str = "pathology",
    schema_dict: dict[str, Any],
    is_global: bool = False,
    status: str = "active",
    actor_user_id: str | None = None,
) -> ReportTemplate:
    """
    Create a version 1 report template after validating against canonical JSON schema.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tenant_id = None if is_global else tenant_context.tenant_id
    effective_user_id = actor_user_id or tenant_context.user_id

    _check_template_permission(db, tenant_context=tenant_context, actor_user_id=effective_user_id)

    clean_code = (code or "").strip().upper()
    if not clean_code:
        raise ValidationError("Template code is required", field="code")

    clean_name = (name or "").strip()
    if not clean_name:
        raise ValidationError("Template name is required", field="name")

    schema_payload = dict(schema_dict)
    schema_payload["code"] = clean_code
    schema_payload["name"] = clean_name
    schema_payload["category"] = category
    schema_payload["version"] = 1
    schema_payload["status"] = status

    validate_template_schema(schema_payload)

    existing = (
        db.query(ReportTemplate)
        .filter(
            ReportTemplate.tenant_id == tenant_id,
            ReportTemplate.code == clean_code,
            ReportTemplate.version == 1,
        )
        .first()
    )
    if existing:
        raise ConflictError(f"Template with code '{clean_code}' version 1 already exists")

    template = ReportTemplate(
        tenant_id=tenant_id,
        code=clean_code,
        name=clean_name,
        category=category,
        version=1,
        is_global=is_global,
        status=status,
        schema_json=json.dumps(schema_payload),
        created_by=effective_user_id,
    )
    db.add(template)
    db.flush()

    log_audit_event(
        db,
        tenant_id=tenant_context.tenant_id,
        action_code="report_template.created",
        actor_user_id=effective_user_id,
        entity_type="report_template",
        entity_id=template.id,
        after_json={
            "code": template.code,
            "version": template.version,
            "category": template.category,
            "is_global": template.is_global,
        },
    )

    db.commit()
    db.refresh(template)
    return template


def create_new_template_version(
    db: Session,
    *,
    tenant_context: TenantContext,
    template_id: str,
    updated_schema_dict: dict[str, Any],
    reason: str | None = None,
    actor_user_id: str | None = None,
) -> ReportTemplate:
    """
    Create a new immutable version of a report template and supersede previous version.
    """
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    effective_user_id = actor_user_id or tenant_context.user_id
    _check_template_permission(db, tenant_context=tenant_context, actor_user_id=effective_user_id)

    prior = (
        db.query(ReportTemplate)
        .filter(
            ReportTemplate.id == template_id,
            or_(
                ReportTemplate.tenant_id == tenant_context.tenant_id,
                ReportTemplate.is_global.is_(True),
            ),
        )
        .first()
    )
    if not prior:
        raise NotFoundError(f"Report template '{template_id}' not found")

    prior.status = "superseded"
    db.flush()

    new_version_num = prior.version + 1
    new_schema = dict(updated_schema_dict)
    new_schema["code"] = prior.code
    new_schema["name"] = updated_schema_dict.get("name", prior.name)
    new_schema["category"] = updated_schema_dict.get("category", prior.category)
    new_schema["version"] = new_version_num
    new_schema["status"] = "active"

    validate_template_schema(new_schema)

    new_template = ReportTemplate(
        tenant_id=prior.tenant_id,
        code=prior.code,
        name=new_schema["name"],
        category=new_schema["category"],
        version=new_version_num,
        is_global=prior.is_global,
        status="active",
        schema_json=json.dumps(new_schema),
        created_by=effective_user_id,
    )
    db.add(new_template)
    db.flush()

    log_audit_event(
        db,
        tenant_id=tenant_context.tenant_id,
        action_code="report_template.versioned",
        actor_user_id=effective_user_id,
        entity_type="report_template",
        entity_id=new_template.id,
        before_json={"prior_id": prior.id, "prior_version": prior.version, "status": "superseded"},
        after_json={
            "new_id": new_template.id,
            "new_version": new_template.version,
            "reason": reason or "Template updated to new version",
        },
    )

    db.commit()
    db.refresh(new_template)
    return new_template



def get_report_template(
    db: Session,
    *,
    tenant_context: TenantContext,
    template_id: str,
) -> ReportTemplate:
    """Get report template by ID with tenant boundary check."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    tpl = (
        db.query(ReportTemplate)
        .filter(
            ReportTemplate.id == template_id,
            or_(
                ReportTemplate.tenant_id == tenant_context.tenant_id,
                ReportTemplate.is_global.is_(True),
            ),
        )
        .first()
    )
    if not tpl:
        raise NotFoundError(f"Report template '{template_id}' not found")
    return tpl


def list_report_templates(
    db: Session,
    *,
    tenant_context: TenantContext,
    category: str | None = None,
    status: str | None = "active",
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[ReportTemplate], int]:
    """List report templates with tenant isolation, category filters, and bounded pagination."""
    verify_tenant_boundary(tenant_context.tenant_id, tenant_context)
    limit = min(max(1, limit), 100)
    offset = max(0, offset)

    query = db.query(ReportTemplate).filter(
        or_(
            ReportTemplate.tenant_id == tenant_context.tenant_id,
            ReportTemplate.is_global.is_(True),
        )
    )
    if category:
        query = query.filter(ReportTemplate.category == category)
    if status:
        query = query.filter(ReportTemplate.status == status)

    total = query.count()
    items = query.order_by(ReportTemplate.code.asc(), desc(ReportTemplate.version)).offset(offset).limit(limit).all()
    return items, total


"""Tests for P06-01: Report Template JSON Schema and Immutable Versioning."""
import json
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.audit.service import get_audit_logs
from app.db import Base
from app.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.core import Branch, Tenant
from app.models.identity import Permission, Role, RolePermission, User, UserRole
from app.models.reporting import ReportTemplate
from app.reporting.template_service import (
    create_new_template_version,
    create_report_template,
    get_json_schema,
    get_report_template,
    list_report_templates,
    validate_template_schema,
)
from app.security.tenant_guard import TenantContext


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def _valid_template_payload():
    return {
        "code": "PATH-STD",
        "name": "Standard Pathology Report",
        "category": "pathology",
        "version": 1,
        "page": {
            "size": "A4",
            "orientation": "portrait",
            "margins": {"top": 15, "bottom": 15, "left": 15, "right": 15, "unit": "mm"},
            "header_height_mm": 25,
            "footer_height_mm": 20,
        },
        "sections": [
            {
                "id": "sec_header",
                "type": "patient_header",
                "config": {"show_patient_id": True, "show_barcode": True},
            },
            {
                "id": "sec_table",
                "type": "test_table",
                "config": {"columns": ["test_name", "result", "unit", "reference_range", "flag"]},
            },
            {
                "id": "sec_qr",
                "type": "qr_code",
                "config": {"verification_url_pattern": "https://verify.aarozi.com/r/{report_token}"},
            },
            {
                "id": "sec_sig",
                "type": "signature_stamp",
                "config": {"pathologist_name": "Dr. Gregory House", "title": "Chief Pathologist"},
            },
            {
                "id": "sec_footer",
                "type": "footer",
                "config": {"disclaimer": "End of report. Clinically correlate."},
            },
        ],
    }


def _setup_template_env(db: Session):
    t1 = Tenant(name="Premier Lab", code="PL-01", is_active=True)
    t2 = Tenant(name="Apex Lab", code="AL-02", is_active=True)
    db.add_all([t1, t2])
    db.flush()

    branch = Branch(tenant_id=t1.id, name="Main Lab", code="ML-01", is_active=True)
    db.add(branch)
    db.flush()

    perms = [
        Permission(code="report.view", module="reporting", resource="report", action="view", risk_level="normal"),
        Permission(code="report.template.manage", module="reporting", resource="template", action="manage", risk_level="high"),
        Permission(code="report.release", module="reporting", resource="report", action="release", risk_level="critical"),
    ]
    db.add_all(perms)
    db.flush()

    role_admin = Role(tenant_id=t1.id, name="Report Designer", is_system=False)
    role_ro = Role(tenant_id=t1.id, name="Read Only", is_system=False)
    db.add_all([role_admin, role_ro])
    db.flush()

    for p in perms:
        db.add(RolePermission(role_id=role_admin.id, permission_id=p.id, allow=True))
    db.add(RolePermission(role_id=role_ro.id, permission_id=perms[0].id, allow=False))

    user_admin = User(tenant_id=t1.id, email="admin@premier.com", username="admin_rep", hashed_password="pw")
    user_ro = User(tenant_id=t1.id, email="ro@premier.com", username="ro_user", hashed_password="pw")
    db.add_all([user_admin, user_ro])
    db.flush()

    db.add_all([
        UserRole(user_id=user_admin.id, role_id=role_admin.id),
        UserRole(user_id=user_ro.id, role_id=role_ro.id),
    ])

    ctx1 = TenantContext(tenant_id=t1.id, branch_id=branch.id, user_id=user_admin.id)
    ctx1_ro = TenantContext(tenant_id=t1.id, branch_id=branch.id, user_id=user_ro.id)
    ctx2 = TenantContext(tenant_id=t2.id, user_id=str(uuid.uuid4()))

    db.commit()

    return {
        "ctx1": ctx1,
        "ctx1_ro": ctx1_ro,
        "ctx2": ctx2,
    }


def test_json_schema_validation():
    schema = get_json_schema()
    assert schema["title"] == "Aarozi Report Template"

    # Valid payload passes
    payload = _valid_template_payload()
    validate_template_schema(payload)

    # Missing required section field raises ValidationError
    bad_payload = dict(payload)
    bad_payload["sections"] = [{"id": "sec_bad", "type": "unsupported_primitive_type"}]
    with pytest.raises(ValidationError):
        validate_template_schema(bad_payload)

    # Empty sections array raises ValidationError
    bad_payload2 = dict(payload)
    bad_payload2["sections"] = []
    with pytest.raises(ValidationError):
        validate_template_schema(bad_payload2)


def test_template_creation_and_versioning_lifecycle(db_session: Session):
    env = _setup_template_env(db_session)
    ctx1 = env["ctx1"]
    ctx1_ro = env["ctx1_ro"]
    ctx2 = env["ctx2"]

    payload = _valid_template_payload()

    # 1. Unauthorized user cannot create template
    with pytest.raises(ForbiddenError):
        create_report_template(
            db_session,
            tenant_context=ctx1_ro,
            code="PATH-STD",
            name="Standard Pathology Report",
            schema_dict=payload,
        )

    # 2. Authorized user creates Version 1
    tpl_v1 = create_report_template(
        db_session,
        tenant_context=ctx1,
        code="PATH-STD",
        name="Standard Pathology Report",
        schema_dict=payload,
    )
    assert tpl_v1.version == 1
    assert tpl_v1.status == "active"

    # Verify audit event
    logs = get_audit_logs(db_session, tenant_id=ctx1.tenant_id, entity_type="report_template", entity_id=tpl_v1.id)
    assert any(l.action_code == "report_template.created" for l in logs)

    # Duplicate code v1 raises ConflictError
    with pytest.raises(ConflictError):
        create_report_template(
            db_session,
            tenant_context=ctx1,
            code="PATH-STD",
            name="Standard Pathology Report Duplicate",
            schema_dict=payload,
        )

    # 3. Create Version 2 (supersedes Version 1)
    updated_payload = dict(payload)
    updated_payload["sections"].append({
        "id": "sec_barcode",
        "type": "barcode",
        "config": {"format": "CODE128"},
    })

    tpl_v2 = create_new_template_version(
        db_session,
        tenant_context=ctx1,
        template_id=tpl_v1.id,
        updated_schema_dict=updated_payload,
        reason="Added specimen accession barcode block to report header",
    )
    assert tpl_v2.version == 2
    assert tpl_v2.status == "active"

    # Version 1 must be preserved and marked superseded
    db_session.refresh(tpl_v1)
    assert tpl_v1.version == 1
    assert tpl_v1.status == "superseded"

    # 4. Multi-tenant isolation: Tenant 2 cannot access Tenant 1 template
    with pytest.raises(NotFoundError):
        get_report_template(db_session, tenant_context=ctx2, template_id=tpl_v1.id)

    t2_items, t2_count = list_report_templates(db_session, tenant_context=ctx2)
    assert t2_count == 0
    assert len(t2_items) == 0

    # 5. Global templates are visible across tenants
    tpl_global = create_report_template(
        db_session,
        tenant_context=ctx1,
        code="GLOBAL-DEFAULT",
        name="Global Default Report Format",
        schema_dict=payload,
        is_global=True,
    )
    t2_read_global = get_report_template(db_session, tenant_context=ctx2, template_id=tpl_global.id)
    assert t2_read_global.id == tpl_global.id


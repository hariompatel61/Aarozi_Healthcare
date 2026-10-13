"""Tests for P06-05: Controlled Signature and Stamp Elements (Pathologist credentials, rendering, revocation, and RBAC)."""
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.audit.service import get_audit_logs
from app.db import Base
from app.errors import ForbiddenError, NotFoundError, ValidationError
from app.models.core import Branch, Tenant
from app.models.identity import Permission, Role, RolePermission, User, UserRole
from app.models.reporting import DigitalSignature
from app.reporting.signature_service import (
    get_user_digital_signature,
    register_digital_signature,
    render_signature_stamp_element,
    revoke_digital_signature,
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


def _setup_signature_env(db: Session):
    t1 = Tenant(name="Metro Labs", code="ML-01", is_active=True)
    t2 = Tenant(name="Global Labs", code="GL-02", is_active=True)
    db.add_all([t1, t2])
    db.flush()

    branch = Branch(tenant_id=t1.id, name="City Lab", code="CL-01", is_active=True)
    db.add(branch)
    db.flush()

    perms = [
        Permission(code="result.approve", module="pathology", resource="result", action="approve", risk_level="critical"),
        Permission(code="report.release", module="reporting", resource="report", action="release", risk_level="critical"),
        Permission(code="report.view", module="reporting", resource="report", action="view", risk_level="normal"),
    ]
    db.add_all(perms)
    db.flush()

    role_path = Role(tenant_id=t1.id, name="Pathologist", is_system=False)
    role_ro = Role(tenant_id=t1.id, name="Viewer", is_system=False)
    db.add_all([role_path, role_ro])
    db.flush()

    db.add_all([
        RolePermission(role_id=role_path.id, permission_id=perms[0].id, allow=True),
        RolePermission(role_id=role_path.id, permission_id=perms[1].id, allow=True),
        RolePermission(role_id=role_ro.id, permission_id=perms[2].id, allow=True),
    ])

    user_path = User(tenant_id=t1.id, email="doc@metro.com", username="dr_house", hashed_password="pw")
    user_ro = User(tenant_id=t1.id, email="ro@metro.com", username="ro_user", hashed_password="pw")
    db.add_all([user_path, user_ro])
    db.flush()

    db.add_all([
        UserRole(user_id=user_path.id, role_id=role_path.id),
        UserRole(user_id=user_ro.id, role_id=role_ro.id),
    ])

    ctx_path = TenantContext(tenant_id=t1.id, branch_id=branch.id, user_id=user_path.id)
    ctx_ro = TenantContext(tenant_id=t1.id, branch_id=branch.id, user_id=user_ro.id)
    ctx2 = TenantContext(tenant_id=t2.id, user_id=str(uuid.uuid4()))

    db.commit()

    return {
        "ctx_path": ctx_path,
        "ctx_ro": ctx_ro,
        "ctx2": ctx2,
        "user_path": user_path,
        "user_ro": user_ro,
    }


def test_signature_registration_and_rendering(db_session: Session):
    env = _setup_signature_env(db_session)
    ctx_path = env["ctx_path"]
    user_path = env["user_path"]

    # 1. Register digital signature
    sig = register_digital_signature(
        db_session,
        tenant_context=ctx_path,
        user_id=user_path.id,
        name="Dr. Gregory House",
        qualifications="MD, FRCPath",
        designation="Consultant Clinical Pathologist",
        registration_no="GMC-882109",
        stamp_text="ELECTRONICALLY SIGNED & VERIFIED",
    )

    assert sig.id is not None
    assert sig.name == "Dr. Gregory House"
    assert sig.status == "active"

    # Check audit log
    logs = get_audit_logs(db_session, tenant_id=ctx_path.tenant_id, entity_type="digital_signature", entity_id=sig.id)
    assert any(l.action_code == "digital_signature.registered" for l in logs)

    # 2. Render signature stamp element
    stamp = render_signature_stamp_element(sig)
    assert stamp["name"] == "Dr. Gregory House"
    assert stamp["registration_no"] == "GMC-882109"
    assert "Digitally signed" in stamp["html_markup"]
    assert "MD, FRCPath" in stamp["html_markup"]


def test_signature_revocation_and_rbac(db_session: Session):
    env = _setup_signature_env(db_session)
    ctx_path = env["ctx_path"]
    ctx_ro = env["ctx_ro"]
    ctx2 = env["ctx2"]
    user_path = env["user_path"]

    # Unauthorized user cannot register signature
    with pytest.raises(ForbiddenError):
        register_digital_signature(
            db_session,
            tenant_context=ctx_ro,
            user_id=user_path.id,
            name="Dr. Read Only",
        )

    # Pathologist registers
    sig = register_digital_signature(
        db_session,
        tenant_context=ctx_path,
        user_id=user_path.id,
        name="Dr. Gregory House",
        registration_no="GMC-882109",
    )

    # Revocation requires mandatory reason
    with pytest.raises(ValidationError):
        revoke_digital_signature(db_session, tenant_context=ctx_path, signature_id=sig.id, reason="   ")

    # Pathologist revokes signature
    revoked = revoke_digital_signature(
        db_session,
        tenant_context=ctx_path,
        signature_id=sig.id,
        reason="Key renewal / certificate expiration",
    )
    assert revoked.status == "revoked"

    # Revoked signature cannot be retrieved via get_user_digital_signature
    with pytest.raises(NotFoundError):
        get_user_digital_signature(db_session, tenant_context=ctx_path, user_id=user_path.id)

    # Multi-tenant isolation: Tenant 2 cannot access Tenant 1 signature
    with pytest.raises(NotFoundError):
        revoke_digital_signature(db_session, tenant_context=ctx2, signature_id=sig.id, reason="Cross-tenant breach")


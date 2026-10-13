"""Tests for P06-08: Multi-Channel Report Delivery Adapters, RBAC, and Transmission History."""
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
from app.models.patient import Patient
from app.models.reporting import Report
from app.reporting.delivery_service import (
    deliver_report,
    get_report_delivery_history,
    list_report_deliveries,
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


def _setup_delivery_env(db: Session):
    t1 = Tenant(name="Metro Labs", code="ML-01", is_active=True)
    t2 = Tenant(name="Global Labs", code="GL-02", is_active=True)
    db.add_all([t1, t2])
    db.flush()

    branch = Branch(tenant_id=t1.id, name="City Central Branch", code="CC-01", is_active=True)
    db.add(branch)
    db.flush()

    perms = [
        Permission(code="report.view", module="reporting", resource="report", action="view", risk_level="normal"),
        Permission(code="report.print", module="reporting", resource="report", action="print", risk_level="normal"),
        Permission(code="report.download", module="reporting", resource="report", action="download", risk_level="normal"),
        Permission(code="report.release", module="reporting", resource="report", action="release", risk_level="critical"),
    ]
    db.add_all(perms)
    db.flush()

    # User 1: Full reporting access (print + download + view + release)
    role_full = Role(tenant_id=t1.id, name="Dispatcher", is_system=False)
    # User 2: View only (no print, no download)
    role_view_only = Role(tenant_id=t1.id, name="View Only", is_system=False)
    db.add_all([role_full, role_view_only])
    db.flush()

    for p in perms:
        db.add(RolePermission(role_id=role_full.id, permission_id=p.id, allow=True))
    db.add(RolePermission(role_id=role_view_only.id, permission_id=perms[0].id, allow=True))

    user_full = User(tenant_id=t1.id, email="dispatch@metro.com", username="dispatcher", hashed_password="pw")
    user_view = User(tenant_id=t1.id, email="view@metro.com", username="viewer_only", hashed_password="pw")
    db.add_all([user_full, user_view])
    db.flush()

    db.add_all([
        UserRole(user_id=user_full.id, role_id=role_full.id),
        UserRole(user_id=user_view.id, role_id=role_view_only.id),
    ])

    ctx_full = TenantContext(tenant_id=t1.id, branch_id=branch.id, user_id=user_full.id)
    ctx_view = TenantContext(tenant_id=t1.id, branch_id=branch.id, user_id=user_view.id)
    ctx2 = TenantContext(tenant_id=t2.id, user_id=str(uuid.uuid4()))

    patient = Patient(tenant_id=t1.id, patient_no="PAT-771", first_name="Rosalind", last_name="Franklin", sex="female")
    db.add(patient)
    db.flush()

    report = Report(
        tenant_id=t1.id,
        patient_id=patient.id,
        report_no="REP-2026-8812",
        status="released",
        released_at=datetime.now(timezone.utc),
        qr_token="VRF-ROSA-1",
    )
    db.add(report)
    db.commit()

    return {
        "ctx_full": ctx_full,
        "ctx_view": ctx_view,
        "ctx2": ctx2,
        "report": report,
    }


def test_multi_channel_report_delivery_and_audit(db_session: Session):
    env = _setup_delivery_env(db_session)
    ctx = env["ctx_full"]
    rep = env["report"]

    # 1. Print dispatch
    del_print = deliver_report(
        db_session,
        tenant_context=ctx,
        report_id=rep.id,
        channel="print",
        recipient="HP-LaserJet-Lab1",
    )
    assert del_print.channel == "print"
    assert del_print.status == "printed"
    assert del_print.recipient == "HP-LaserJet-Lab1"

    # Audit check for print
    logs = get_audit_logs(db_session, tenant_id=ctx.tenant_id, entity_type="report_delivery", entity_id=del_print.id)
    assert any(l.action_code == "report.printed" for l in logs)

    # 2. Email dispatch
    del_email = deliver_report(
        db_session,
        tenant_context=ctx,
        report_id=rep.id,
        channel="email",
        recipient="patient.rosalind@example.com",
    )
    assert del_email.channel == "email"
    assert del_email.status == "sent"

    # 3. SMS dispatch
    del_sms = deliver_report(
        db_session,
        tenant_context=ctx,
        report_id=rep.id,
        channel="sms",
        recipient="+15551234567",
    )
    assert del_sms.channel == "sms"

    # 4. WhatsApp dispatch
    del_wa = deliver_report(
        db_session,
        tenant_context=ctx,
        report_id=rep.id,
        channel="whatsapp",
        recipient="+15551234567",
    )
    assert del_wa.channel == "whatsapp"

    # 5. Check delivery history
    history = get_report_delivery_history(db_session, tenant_context=ctx, report_id=rep.id)
    assert len(history) == 4
    channels_used = {h.channel for h in history}
    assert channels_used == {"print", "email", "sms", "whatsapp"}


def test_delivery_validations_rbac_and_tenant_isolation(db_session: Session):
    env = _setup_delivery_env(db_session)
    ctx_full = env["ctx_full"]
    ctx_view = env["ctx_view"]
    ctx2 = env["ctx2"]
    rep = env["report"]

    # 1. Unsupported channel rejected
    with pytest.raises(ValidationError):
        deliver_report(
            db_session,
            tenant_context=ctx_full,
            report_id=rep.id,
            channel="carrier_pigeon",
            recipient="Somewhere",
        )

    # 2. Empty recipient rejected
    with pytest.raises(ValidationError):
        deliver_report(
            db_session,
            tenant_context=ctx_full,
            report_id=rep.id,
            channel="email",
            recipient="   ",
        )

    # 3. View-only user cannot print without report.print permission
    with pytest.raises(ForbiddenError):
        deliver_report(
            db_session,
            tenant_context=ctx_view,
            report_id=rep.id,
            channel="print",
            recipient="Printer-1",
        )

    # 4. View-only user cannot download without report.download permission
    with pytest.raises(ForbiddenError):
        deliver_report(
            db_session,
            tenant_context=ctx_view,
            report_id=rep.id,
            channel="download",
            recipient="browser_export",
        )

    # 5. Multi-tenant isolation: Tenant 2 cannot deliver Tenant 1 report
    with pytest.raises(NotFoundError):
        deliver_report(
            db_session,
            tenant_context=ctx2,
            report_id=rep.id,
            channel="email",
            recipient="hacker@ext.com",
        )

    t2_history = get_report_delivery_history(db_session, tenant_context=ctx2, report_id=rep.id)
    assert len(t2_history) == 0


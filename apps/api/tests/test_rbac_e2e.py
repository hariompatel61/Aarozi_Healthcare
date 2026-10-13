"""E2E RBAC and concurrency tests across 4 concurrent users (P02-10)."""

from __future__ import annotations

import concurrent.futures
import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.models.core import Tenant, Branch
from app.models.identity import User, Permission
from app.rbac.permissions import get_all_permissions
from app.rbac.service import create_role
from app.rbac.scope import assign_role_to_user
from app.rbac.engine import authorize_action, enforce_permission
from app.audit.service import log_audit_event, get_audit_logs
from app.errors import ForbiddenError


@pytest.fixture
def db_session_factory(tmp_path):
    db_file = tmp_path / "test_rbac.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False, "timeout": 30},
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    try:
        yield session_factory
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()




def seed_env(session: Session):
    tenant = Tenant(name="Alpha Diagnostics", code="ADC01")
    session.add(tenant)
    session.flush()

    branch = Branch(tenant_id=tenant.id, name="Main Lab", code="ADC-M")
    session.add(branch)
    session.flush()

    perm_map = {}
    for p in get_all_permissions():
        perm = Permission(code=p["code"], module=p["module"], resource=p["resource"], action=p["action"], risk_level=p["risk_level"])
        session.add(perm)
        perm_map[p["code"]] = perm
    session.flush()

    r1 = create_role(session, tenant_id=tenant.id, name="Receptionist", permission_ids=[perm_map["patient.create"].id, perm_map["order.create"].id])
    r2 = create_role(session, tenant_id=tenant.id, name="Phlebotomist", permission_ids=[perm_map["sample.collect"].id])
    r3 = create_role(session, tenant_id=tenant.id, name="Pathologist", permission_ids=[perm_map["result.approve"].id, perm_map["report.release"].id])
    r4 = create_role(session, tenant_id=tenant.id, name="Billing Clerk", permission_ids=[perm_map["billing.discount"].id])

    u1 = User(tenant_id=tenant.id, username="rec1", email="rec@adc.test", hashed_password="pw")
    u2 = User(tenant_id=tenant.id, username="phleb1", email="phleb@adc.test", hashed_password="pw")
    u3 = User(tenant_id=tenant.id, username="path1", email="path@adc.test", hashed_password="pw")
    u4 = User(tenant_id=tenant.id, username="bill1", email="bill@adc.test", hashed_password="pw")

    session.add_all([u1, u2, u3, u4])
    session.flush()

    for u, r in [(u1, r1), (u2, r2), (u3, r3), (u4, r4)]:
        assign_role_to_user(session, user_id=u.id, role_id=r.id, branch_ids=[branch.id])

    session.commit()
    return {"tenant_id": tenant.id, "branch_id": branch.id, "u1": u1.id, "u2": u2.id, "u3": u3.id, "u4": u4.id}


def test_concurrent_4_users_rbac(db_session_factory):
    setup_s = db_session_factory()
    env = seed_env(setup_s)
    setup_s.close()

    def run_receptionist():
        s = db_session_factory()
        u = s.get(User, env["u1"])
        assert authorize_action(s, u, "patient.create", branch_id=env["branch_id"]) is True
        log_audit_event(s, tenant_id=env["tenant_id"], actor_user_id=u.id, action_code="patient.create")
        with pytest.raises(ForbiddenError):
            enforce_permission(s, u, "result.approve")
        s.close()
        return True

    def run_phlebotomist():
        s = db_session_factory()
        u = s.get(User, env["u2"])
        assert authorize_action(s, u, "sample.collect", branch_id=env["branch_id"]) is True
        log_audit_event(s, tenant_id=env["tenant_id"], actor_user_id=u.id, action_code="sample.collect")
        with pytest.raises(ForbiddenError):
            enforce_permission(s, u, "billing.discount")
        s.close()
        return True

    def run_pathologist():
        s = db_session_factory()
        u = s.get(User, env["u3"])
        assert authorize_action(s, u, "result.approve", branch_id=env["branch_id"]) is True
        log_audit_event(s, tenant_id=env["tenant_id"], actor_user_id=u.id, action_code="result.approve")
        with pytest.raises(ForbiddenError):
            enforce_permission(s, u, "patient.create")
        s.close()
        return True

    def run_billing():
        s = db_session_factory()
        u = s.get(User, env["u4"])
        assert authorize_action(s, u, "billing.discount", branch_id=env["branch_id"]) is True
        log_audit_event(s, tenant_id=env["tenant_id"], actor_user_id=u.id, action_code="billing.discount")
        with pytest.raises(ForbiddenError):
            enforce_permission(s, u, "sample.collect")
        s.close()
        return True

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        futs = [ex.submit(fn) for fn in [run_receptionist, run_phlebotomist, run_pathologist, run_billing]]
        assert all(f.result() for f in futs)

    chk_s = db_session_factory()
    logs = get_audit_logs(chk_s, tenant_id=env["tenant_id"])
    actions = {a.action_code for a in logs}
    assert {"patient.create", "sample.collect", "result.approve", "billing.discount"} <= actions
    chk_s.close()

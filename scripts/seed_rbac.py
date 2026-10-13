"""Seed script to initialize and configure local database and RBAC permissions."""
from __future__ import annotations
import os, sys, uuid
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "apps" / "api"))
sys.path.insert(0, str(repo_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.db import Base
from app.models.core import Branch, Department, Tenant
from app.models.identity import Permission, Role, RolePermission, User, UserRole
from app.rbac.permissions import PERMISSIONS_CATALOG

def get_sync_db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url or "postgresql+asyncpg" in url:
        dev_db = repo_root / "apps" / "api" / "dev_aarozi.db"
        return f"sqlite:///{dev_db}"
    return url.replace("asyncpg", "psycopg2") if "asyncpg" in url else url

def run_seed():
    db_url = get_sync_db_url()
    print(f"[*] Target Database: {db_url}")
    engine = create_engine(db_url)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        tenant = session.query(Tenant).filter_by(code="AAROZI_HQ").first()
        if not tenant:
            tenant = Tenant(id=str(uuid.uuid4()), name="Aarozi Central Diagnostics", code="AAROZI_HQ", is_active=True)
            session.add(tenant)
            session.flush()

        branch = session.query(Branch).filter_by(tenant_id=tenant.id, code="BRANCH_01").first()
        if not branch:
            branch = Branch(id=str(uuid.uuid4()), tenant_id=tenant.id, name="Main Branch", code="BRANCH_01", is_active=True)
            session.add(branch)
            session.flush()

        dept = session.query(Department).filter_by(branch_id=branch.id, code="DEPT_PATH").first()
        if not dept:
            dept = Department(id=str(uuid.uuid4()), tenant_id=tenant.id, branch_id=branch.id, name="Pathology Lab", code="DEPT_PATH", is_active=True)
            session.add(dept)
            session.flush()

        perm_map = {}
        for p in PERMISSIONS_CATALOG:
            db_p = session.query(Permission).filter_by(code=p["code"]).first()
            if not db_p:
                db_p = Permission(id=str(uuid.uuid4()), code=p["code"], module=p["module"], resource=p["resource"], action=p["action"], risk_level=p.get("risk_level", "normal"))
                session.add(db_p)
                session.flush()
            perm_map[db_p.code] = db_p

        roles = [
            ("Tenant Administrator", True, list(perm_map.keys())),
            ("Pathologist", False, ["sample.receive", "result.enter", "result.approve", "report.generate", "report.sign"]),
            ("Phlebotomist", False, ["patient.view", "order.create", "sample.collect", "sample.receive"]),
            ("Receptionist", False, ["patient.create", "patient.view", "order.create", "order.cancel"]),
            ("Billing Clerk", False, ["patient.view", "order.create", "invoice.create", "payment.collect", "billing.discount"]),
        ]

        role_objs = {}
        for rname, issys, p_codes in roles:
            r = session.query(Role).filter_by(tenant_id=tenant.id, name=rname).first()
            if not r:
                r = Role(id=str(uuid.uuid4()), tenant_id=tenant.id, name=rname, is_system=issys, status="active")
                session.add(r)
                session.flush()
            role_objs[rname] = r
            for pc in p_codes:
                p_item = perm_map.get(pc)
                if p_item and not session.query(RolePermission).filter_by(role_id=r.id, permission_id=p_item.id).first():
                    session.add(RolePermission(role_id=r.id, permission_id=p_item.id, allow=True))

        users = [
            ("admin", "admin@aarozi.local", "Super Admin", "Tenant Administrator", ["*"]),
            ("dr.sarah", "sarah@aarozi.local", "Dr. Sarah", "Pathologist", [branch.id]),
            ("john.phleb", "john@aarozi.local", "John Doe", "Phlebotomist", [branch.id]),
            ("mary.rec", "mary@aarozi.local", "Mary Smith", "Receptionist", [branch.id]),
        ]
        for uname, umail, fname, rname, scopes in users:
            u = session.query(User).filter_by(tenant_id=tenant.id, username=uname).first()
            if not u:
                u = User(id=str(uuid.uuid4()), tenant_id=tenant.id, username=uname, email=umail, hashed_password="pw_hash_demo", full_name=fname, is_active=True, is_superuser=(uname=="admin"))
                session.add(u)
                session.flush()
            target_role = role_objs.get(rname)
            if target_role and not session.query(UserRole).filter_by(user_id=u.id, role_id=target_role.id).first():
                session.add(UserRole(user_id=u.id, role_id=target_role.id, branch_scope_json=scopes, department_scope_json=["*"]))

        session.commit()
    print("[SUCCESS] Seeded Tenant, Branch, Department, Permissions, Roles, and Demo Users.")

if __name__ == "__main__":
    run_seed()

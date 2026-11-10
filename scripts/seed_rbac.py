"""Seed script to initialize and configure local database and RBAC permissions."""
from __future__ import annotations
import os, sys, uuid, datetime
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "apps" / "api"))
sys.path.insert(0, str(repo_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import app.models
from app.db import Base
from app.models.core import Branch, Department, Tenant
from app.models.identity import Permission, Role, RolePermission, User, UserRole
from app.models.pathology import Test, TestReferenceRange
from app.models.patient import Patient
from app.models.billing import PriceList, PriceListItem
from app.rbac.permissions import PERMISSIONS_CATALOG
from app.security.auth import hash_password

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

        valid_pw_hash = hash_password("Admin@12345")
        users = [
            ("superadmin@aarozi.in", "superadmin@aarozi.in", "Super Administrator", "Tenant Administrator", ["*"]),
            ("admin@aarozi.com", "admin@aarozi.com", "Super Administrator", "Tenant Administrator", ["*"]),
            ("admin", "admin@aarozi.local", "Super Admin", "Tenant Administrator", ["*"]),
            ("dr.sarah", "sarah@aarozi.local", "Dr. Sarah", "Pathologist", [branch.id]),
            ("john.phleb", "john@aarozi.local", "John Doe", "Phlebotomist", [branch.id]),
            ("mary.rec", "mary@aarozi.local", "Mary Smith", "Receptionist", [branch.id]),
        ]
        for uname, umail, fname, rname, scopes in users:
            u = session.query(User).filter_by(tenant_id=tenant.id, username=uname).first()
            if not u:
                u = User(id=str(uuid.uuid4()), tenant_id=tenant.id, username=uname, email=umail, hashed_password=valid_pw_hash, full_name=fname, is_active=True, is_superuser=("admin" in uname or "super" in uname))
                session.add(u)
                session.flush()
            else:
                u.hashed_password = valid_pw_hash
                session.flush()

            target_role = role_objs.get(rname)
            if target_role and not session.query(UserRole).filter_by(user_id=u.id, role_id=target_role.id).first():
                session.add(UserRole(user_id=u.id, role_id=target_role.id, branch_scope_json=scopes, department_scope_json=["*"]))

        # Seed Sample Pathology Tests
        sample_tests = [
            ("CBC", "Complete Blood Count", "CBC", "Whole Blood", "EDTA Lavender", "Hemology Analyzer", "10^3/uL", 2),
            ("GLU_F", "Fasting Blood Glucose", "FBG", "Fluoride Plasma", "Grey Top", "Hexokinase", "mg/dL", 1),
            ("LIPID", "Lipid Profile", "Lipid", "Serum", "Red/SST", "Enzymatic", "mg/dL", 2),
            ("TSH", "Thyroid Stimulating Hormone", "TSH", "Serum", "Red/SST", "CLIA", "uIU/mL", 2),
            ("CREAT", "Serum Creatinine", "Creatinine", "Serum", "Red/SST", "Jaffe Modified", "mg/dL", 2),
        ]
        test_objs = {}
        for code, name, sname, spec, cont, meth, unit, prec in sample_tests:
            t = session.query(Test).filter_by(tenant_id=tenant.id, code=code).first()
            if not t:
                t = Test(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant.id,
                    department_id=dept.id,
                    code=code,
                    name=name,
                    display_name=name,
                    short_name=sname,
                    specimen_type=spec,
                    container_type=cont,
                    method=meth,
                    unit=unit,
                    decimal_precision=prec,
                    status="active",
                    version=1,
                )
                session.add(t)
                session.flush()
            test_objs[code] = t

        # Seed Reference Range for Fasting Glucose
        glu_test = test_objs.get("GLU_F")
        if glu_test and not session.query(TestReferenceRange).filter_by(test_id=glu_test.id).first():
            session.add(TestReferenceRange(
                id=str(uuid.uuid4()),
                test_id=glu_test.id,
                sex="all",
                age_min=0,
                age_max=43800,
                low_value=70.0,
                high_value=99.0,
                critical_low=45.0,
                critical_high=400.0,
                text_range="70 - 99 mg/dL",
            ))

        # Seed Default Price List
        plist = session.query(PriceList).filter_by(tenant_id=tenant.id, code="STANDARD").first()
        if not plist:
            plist = PriceList(
                id=str(uuid.uuid4()),
                tenant_id=tenant.id,
                code="STANDARD",
                name="Standard Retail Tariff",
                is_default=True,
                status="active",
            )
            session.add(plist)
            session.flush()

            test_prices = {"CBC": 350.0, "GLU_F": 120.0, "LIPID": 850.0, "TSH": 450.0, "CREAT": 200.0}
            for code, prc in test_prices.items():
                t = test_objs.get(code)
                if t:
                    session.add(PriceListItem(
                        id=str(uuid.uuid4()),
                        tenant_id=tenant.id,
                        price_list_id=plist.id,
                        item_type="test",
                        item_id=t.id,
                        rate=prc,
                        min_rate=prc * 0.8,
                    ))

        # Seed Demo Patients
        demo_patients = [
            ("P-20261016-0001", "Aarav", "Sharma", "male", datetime.date(1990, 5, 12), "9876543210", "aarav@example.com", "O+"),
            ("P-20261016-0002", "Priya", "Verma", "female", datetime.date(1996, 8, 24), "9876543211", "priya@example.com", "A+"),
            ("P-20261016-0003", "Rajesh", "Gupta", "male", datetime.date(1972, 11, 3), "9876543212", "rajesh@example.com", "B+"),
        ]
        for pno, fname, lname, sex, dob, mob, eml, bg in demo_patients:
            p = session.query(Patient).filter_by(tenant_id=tenant.id, patient_no=pno).first()
            if not p:
                session.add(Patient(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant.id,
                    branch_id=branch.id,
                    patient_no=pno,
                    first_name=fname,
                    last_name=lname,
                    sex=sex,
                    date_of_birth=dob,
                    mobile_normalized=mob,
                    email=eml,
                    blood_group=bg,
                    status="active",
                ))

        session.commit()
    print("[SUCCESS] Seeded Tenant, Branch, Department, Permissions, Roles, Users (password: admin123), Tests, Price Lists, and Patients.")

if __name__ == "__main__":
    run_seed()

"""Comprehensive seed script for Aarozi Healthcare database.
Populates realistic operational clinical data:
- Tenant, Branch, Department, Roles, Permissions, Users
- Test Master Catalog with Reference Ranges
- Patients Master Directory
- Orders, Order Items
- Samples with Sample Collection Time (collected_at)
- Results and Result Values with normal/abnormal flags
- Diagnostic Reports with Report Generation Time (released_at / created_at)
- Billing Invoices and Payments
- Blood Bank Inventory Units
"""
from __future__ import annotations

import os
import sys
import uuid
import datetime
from pathlib import Path
from decimal import Decimal

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "apps" / "api"))
sys.path.insert(0, str(repo_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import app.models
from app.db import Base
from app.models.core import Tenant, Branch, Department
from app.models.identity import User, Role, Permission, RolePermission, UserRole
from app.models.patient import Patient
from app.models.pathology import (
    Test, TestReferenceRange, Order, OrderItem, Sample, Result, ResultValue
)
from app.models.reporting import ReportTemplate, Report
from app.models.billing import PriceList, PriceListItem, Invoice, Payment
from app.models.blood_bank import Donor, Donation, BloodUnit
from app.rbac.permissions import PERMISSIONS_CATALOG
from app.security.auth import hash_password


def get_sync_db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url or "postgresql+asyncpg" in url:
        dev_db = repo_root / "apps" / "api" / "dev_aarozi.db"
        return f"sqlite:///{dev_db}"
    return url.replace("asyncpg", "psycopg2") if "asyncpg" in url else url


def seed_database():
    db_url = get_sync_db_url()
    print(f"[*] Target Database: {db_url}")
    engine = create_engine(db_url, connect_args={"check_same_thread": False} if "sqlite" in db_url else {})
    Base.metadata.create_all(bind=engine)

    today = datetime.date.today()
    now = datetime.datetime.now(datetime.timezone.utc)

    with Session(engine) as session:
        # 1. Tenant, Branch, Department
        tenant = session.query(Tenant).filter_by(code="AAROZI_HQ").first()
        if not tenant:
            tenant = Tenant(
                id="ten_aarozi_hq",
                name="Aarozi Central Diagnostics",
                code="AAROZI_HQ",
                is_active=True,
            )
            session.add(tenant)
            session.flush()

        branch = session.query(Branch).filter_by(tenant_id=tenant.id, code="BRANCH_01").first()
        if not branch:
            branch = Branch(
                id="br_main_01",
                tenant_id=tenant.id,
                name="Main City Branch",
                code="BRANCH_01",
                is_active=True,
            )
            session.add(branch)
            session.flush()

        dept_path = session.query(Department).filter_by(branch_id=branch.id, code="DEPT_PATH").first()
        if not dept_path:
            dept_path = Department(
                id="dep_path_01",
                tenant_id=tenant.id,
                branch_id=branch.id,
                name="Pathology & Laboratory",
                code="DEPT_PATH",
                is_active=True,
            )
            session.add(dept_path)
            session.flush()

        dept_hem = session.query(Department).filter_by(branch_id=branch.id, code="DEPT_HEM").first()
        if not dept_hem:
            dept_hem = Department(
                id="dep_hem_01",
                tenant_id=tenant.id,
                branch_id=branch.id,
                name="Hematology",
                code="DEPT_HEM",
                is_active=True,
            )
            session.add(dept_hem)
            session.flush()

        dept_bio = session.query(Department).filter_by(branch_id=branch.id, code="DEPT_BIO").first()
        if not dept_bio:
            dept_bio = Department(
                id="dep_bio_01",
                tenant_id=tenant.id,
                branch_id=branch.id,
                name="Biochemistry",
                code="DEPT_BIO",
                is_active=True,
            )
            session.add(dept_bio)
            session.flush()

        # 2. Permissions & Roles
        perm_map = {}
        for p in PERMISSIONS_CATALOG:
            db_p = session.query(Permission).filter_by(code=p["code"]).first()
            if not db_p:
                db_p = Permission(
                    id=str(uuid.uuid4()),
                    code=p["code"],
                    module=p["module"],
                    resource=p["resource"],
                    action=p["action"],
                    risk_level=p.get("risk_level", "normal"),
                )
                session.add(db_p)
                session.flush()
            perm_map[db_p.code] = db_p

        roles_config = [
            ("Tenant Administrator", True, list(perm_map.keys())),
            ("Pathologist", False, ["sample.receive", "result.enter", "result.verify", "result.approve", "report.generate", "report.sign", "report.release"]),
            ("Phlebotomist", False, ["patient.view", "order.create", "order.view", "sample.collect", "sample.receive"]),
            ("Receptionist", False, ["patient.create", "patient.view", "order.create", "order.view", "order.cancel"]),
            ("Billing Clerk", False, ["patient.view", "order.create", "invoice.create", "payment.collect", "billing.discount"]),
        ]

        role_objs = {}
        for rname, issys, p_codes in roles_config:
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

        # 3. Users with valid hashed password ("Admin@12345")
        valid_pw = hash_password("Admin@12345")
        user_definitions = [
            ("superadmin@aarozi.in", "superadmin@aarozi.in", "Super Administrator", "Tenant Administrator", ["*"]),
            ("admin@aarozi.com", "admin@aarozi.com", "Super Administrator", "Tenant Administrator", ["*"]),
            ("admin", "admin@aarozi.local", "Super Admin", "Tenant Administrator", ["*"]),
            ("dr.sarah", "sarah@aarozi.local", "Dr. Sarah Khan", "Pathologist", [branch.id]),
            ("john.phleb", "john@aarozi.local", "John Doe", "Phlebotomist", [branch.id]),
            ("mary.rec", "mary@aarozi.local", "Mary Smith", "Receptionist", [branch.id]),
        ]
        user_objs = {}
        for uname, umail, fname, rname, scopes in user_definitions:
            u = session.query(User).filter_by(tenant_id=tenant.id, username=uname).first()
            if not u:
                u = User(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant.id,
                    username=uname,
                    email=umail,
                    hashed_password=valid_pw,
                    full_name=fname,
                    is_active=True,
                    is_superuser=("admin" in uname or "super" in uname),
                )
                session.add(u)
                session.flush()
            else:
                u.hashed_password = valid_pw
                session.flush()
            user_objs[uname] = u

            target_role = role_objs.get(rname)
            if target_role and not session.query(UserRole).filter_by(user_id=u.id, role_id=target_role.id).first():
                session.add(UserRole(
                    user_id=u.id,
                    role_id=target_role.id,
                    branch_scope_json=scopes,
                    department_scope_json=["*"],
                ))

        # 4. Diagnostic Tests Master Catalog
        test_defs = [
            ("CBC", "Complete Blood Count", "CBC", dept_hem.id, "Whole Blood", "EDTA Lavender", "Sysmex XN-550", "10^3/uL", 2, 350.0),
            ("GLU_F", "Fasting Blood Glucose", "FBG", dept_bio.id, "Fluoride Plasma", "Grey Top", "Hexokinase", "mg/dL", 1, 120.0),
            ("LIPID", "Lipid Profile", "Lipid", dept_bio.id, "Serum", "Red/SST", "Enzymatic Colorimetric", "mg/dL", 2, 850.0),
            ("TSH", "Thyroid Stimulating Hormone", "TSH", dept_bio.id, "Serum", "SST Yellow", "CLIA", "uIU/mL", 2, 450.0),
            ("CREAT", "Serum Creatinine", "Creatinine", dept_bio.id, "Serum", "SST Yellow", "Jaffe Modified", "mg/dL", 2, 200.0),
            ("HBA1C", "Glycated Hemoglobin (HbA1c)", "HbA1c", dept_hem.id, "Whole Blood", "EDTA Lavender", "HPLC Biorad", "%", 1, 650.0),
            ("VITD", "Vitamin D (25-OH)", "Vit-D", dept_bio.id, "Serum", "SST Yellow", "CLIA", "ng/mL", 1, 1200.0),
        ]
        test_map = {}
        for code, name, sname, did, spec, cont, meth, unit, prec, price in test_defs:
            t = session.query(Test).filter_by(tenant_id=tenant.id, code=code).first()
            if not t:
                t = Test(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant.id,
                    department_id=did,
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
            test_map[code] = t

        # Reference Ranges
        ranges = [
            ("GLU_F", 70.0, 99.0, 45.0, 400.0, "70.0 - 99.0 mg/dL"),
            ("HBA1C", 4.0, 5.6, 3.5, 14.0, "4.0 - 5.6 % (Normal)"),
            ("TSH", 0.4, 4.2, 0.1, 20.0, "0.40 - 4.20 uIU/mL"),
            ("CREAT", 0.7, 1.2, 0.4, 5.0, "0.7 - 1.2 mg/dL"),
        ]
        for tcode, low, high, clow, chigh, trange in ranges:
            t_obj = test_map.get(tcode)
            if t_obj and not session.query(TestReferenceRange).filter_by(test_id=t_obj.id).first():
                session.add(TestReferenceRange(
                    id=str(uuid.uuid4()),
                    test_id=t_obj.id,
                    sex="all",
                    age_min=0,
                    age_max=120,
                    age_unit="years",
                    low_value=Decimal(str(low)),
                    high_value=Decimal(str(high)),
                    critical_low=Decimal(str(clow)),
                    critical_high=Decimal(str(chigh)),
                    text_range=trange,
                ))

        # Default Price List
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
            for code, name, sname, did, spec, cont, meth, unit, prec, price in test_defs:
                t = test_map.get(code)
                if t:
                    session.add(PriceListItem(
                        id=str(uuid.uuid4()),
                        tenant_id=tenant.id,
                        price_list_id=plist.id,
                        item_type="test",
                        item_id=t.id,
                        rate=price,
                        min_rate=price * 0.8,
                    ))

        # 5. Patients Master Data
        patient_data = [
            ("PAT250001", "Aarav", "Sharma", "male", datetime.date(1990, 5, 12), "9811223344", "aarav.sharma@example.com", "O+"),
            ("PAT250002", "Priya", "Verma", "female", datetime.date(1996, 8, 24), "9822334455", "priya.verma@example.com", "A+"),
            ("PAT250003", "Rajesh", "Mehta", "male", datetime.date(1979, 11, 3), "9833445566", "rajesh.mehta@example.com", "B+"),
            ("PAT250004", "Kavita", "Singh", "female", datetime.date(1993, 2, 17), "9844556677", "kavita.singh@example.com", "AB+"),
            ("PAT250005", "Suresh", "Gupta", "male", datetime.date(1972, 7, 29), "9855667788", "suresh.gupta@example.com", "O-"),
            ("PAT250006", "Ananya", "Roy", "female", datetime.date(2000, 10, 14), "9866778899", "ananya.roy@example.com", "B-"),
        ]
        patient_map = {}
        for pno, fname, lname, sex, dob, mob, eml, bg in patient_data:
            p = session.query(Patient).filter_by(tenant_id=tenant.id, patient_no=pno).first()
            if not p:
                p = Patient(
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
                )
                session.add(p)
                session.flush()
            patient_map[pno] = p

        # 6. Orders, Samples, Results, and Reports with Real Timestamps
        # Today's operational timeline
        time_base = datetime.datetime.combine(today, datetime.time(8, 0), tzinfo=datetime.timezone.utc)

        clinical_cases = [
            {
                "patient_no": "PAT250001",
                "order_no": "ORD250001",
                "tests": ["CBC", "GLU_F"],
                "total_amount": 470.0,
                "order_status": "completed",
                "order_time": time_base + datetime.timedelta(hours=1, minutes=10),     # 09:10 AM
                "sample_barcode": "SMP250001",
                "specimen": "EDTA Whole Blood / Fluoride",
                "tube_color": "#8b5cf6",
                "sample_status": "completed",
                "sample_collection_time": time_base + datetime.timedelta(hours=1, minutes=15), # 09:15 AM
                "sample_received_time": time_base + datetime.timedelta(hours=1, minutes=30),   # 09:30 AM
                "report_no": "REP250001",
                "report_status": "released",
                "report_generation_time": time_base + datetime.timedelta(hours=2, minutes=45), # 10:45 AM
                "results": [
                    {"analyte": "GLU_F", "raw": "94.5", "num": 94.5, "flag": "normal", "unit": "mg/dL"},
                    {"analyte": "CBC_HB", "raw": "14.2", "num": 14.2, "flag": "normal", "unit": "g/dL"},
                ]
            },
            {
                "patient_no": "PAT250002",
                "order_no": "ORD250002",
                "tests": ["TSH"],
                "total_amount": 450.0,
                "order_status": "processing",
                "order_time": time_base + datetime.timedelta(hours=1, minutes=35),     # 09:35 AM
                "sample_barcode": "SMP250002",
                "specimen": "Serum",
                "tube_color": "#eab308",
                "sample_status": "processing",
                "sample_collection_time": time_base + datetime.timedelta(hours=1, minutes=42), # 09:42 AM
                "sample_received_time": time_base + datetime.timedelta(hours=2, minutes=0),    # 10:00 AM
                "report_no": "REP250002",
                "report_status": "draft",
                "report_generation_time": None, # In process, not released yet
                "results": [
                    {"analyte": "TSH", "raw": "5.85", "num": 5.85, "flag": "high", "unit": "uIU/mL"},
                ]
            },
            {
                "patient_no": "PAT250003",
                "order_no": "ORD250003",
                "tests": ["HBA1C", "CREAT"],
                "total_amount": 850.0,
                "order_status": "completed",
                "order_time": time_base + datetime.timedelta(hours=2, minutes=5),      # 10:05 AM
                "sample_barcode": "SMP250003",
                "specimen": "EDTA Whole Blood / Serum",
                "tube_color": "#8b5cf6",
                "sample_status": "completed",
                "sample_collection_time": time_base + datetime.timedelta(hours=2, minutes=15), # 10:15 AM
                "sample_received_time": time_base + datetime.timedelta(hours=2, minutes=30),   # 10:30 AM
                "report_no": "REP250003",
                "report_status": "released",
                "report_generation_time": time_base + datetime.timedelta(hours=3, minutes=30), # 11:30 AM
                "results": [
                    {"analyte": "HBA1C", "raw": "7.8", "num": 7.8, "flag": "high", "unit": "%"},
                    {"analyte": "CREAT", "raw": "0.95", "num": 0.95, "flag": "normal", "unit": "mg/dL"},
                ]
            },
            {
                "patient_no": "PAT250004",
                "order_no": "ORD250004",
                "tests": ["VITD"],
                "total_amount": 1200.0,
                "order_status": "pending",
                "order_time": time_base + datetime.timedelta(hours=2, minutes=20),     # 10:20 AM
                "sample_barcode": "SMP250004",
                "specimen": "Serum",
                "tube_color": "#eab308",
                "sample_status": "pending",
                "sample_collection_time": time_base + datetime.timedelta(hours=2, minutes=28), # 10:28 AM
                "sample_received_time": None,
                "report_no": None,
                "report_status": None,
                "report_generation_time": None,
                "results": []
            },
            {
                "patient_no": "PAT250005",
                "order_no": "ORD250005",
                "tests": ["LIPID"],
                "total_amount": 850.0,
                "order_status": "processing",
                "order_time": time_base + datetime.timedelta(hours=2, minutes=35),     # 10:35 AM
                "sample_barcode": "SMP250005",
                "specimen": "Serum",
                "tube_color": "#ef4444",
                "sample_status": "processing",
                "sample_collection_time": time_base + datetime.timedelta(hours=2, minutes=40), # 10:40 AM
                "sample_received_time": time_base + datetime.timedelta(hours=3, minutes=0),    # 11:00 AM
                "report_no": "REP250005",
                "report_status": "draft",
                "report_generation_time": None,
                "results": [
                    {"analyte": "CHOL", "raw": "242.0", "num": 242.0, "flag": "high", "unit": "mg/dL"},
                ]
            },
            {
                "patient_no": "PAT250006",
                "order_no": "ORD250006",
                "tests": ["CBC"],
                "total_amount": 350.0,
                "order_status": "completed",
                "order_time": time_base + datetime.timedelta(hours=3, minutes=10),     # 11:10 AM
                "sample_barcode": "SMP250006",
                "specimen": "EDTA Whole Blood",
                "tube_color": "#8b5cf6",
                "sample_status": "completed",
                "sample_collection_time": time_base + datetime.timedelta(hours=3, minutes=15), # 11:15 AM
                "sample_received_time": time_base + datetime.timedelta(hours=3, minutes=25),   # 11:25 AM
                "report_no": "REP250006",
                "report_status": "released",
                "report_generation_time": time_base + datetime.timedelta(hours=4, minutes=10), # 12:10 PM
                "results": [
                    {"analyte": "CBC_HB", "raw": "12.8", "num": 12.8, "flag": "normal", "unit": "g/dL"},
                ]
            },
        ]

        phleb_user = user_objs.get("john.phleb")
        path_user = user_objs.get("dr.sarah")

        for case in clinical_cases:
            p_obj = patient_map.get(case["patient_no"])
            if not p_obj:
                continue

            order = session.query(Order).filter_by(tenant_id=tenant.id, order_no=case["order_no"]).first()
            if not order:
                order = Order(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant.id,
                    branch_id=branch.id,
                    patient_id=p_obj.id,
                    order_no=case["order_no"],
                    status=case["order_status"],
                    ordered_at=case["order_time"],
                )
                session.add(order)
                session.flush()

                first_item = None
                for tcode in case["tests"]:
                    t_obj = test_map.get(tcode)
                    if not t_obj:
                        continue
                    item = OrderItem(
                        id=str(uuid.uuid4()),
                        order_id=order.id,
                        test_id=t_obj.id,
                        status=case["order_status"],
                        final_amount=350.0,
                    )
                    session.add(item)
                    session.flush()
                    if not first_item:
                        first_item = item

                # Sample with Sample Collection Time
                if first_item and case.get("sample_barcode"):
                    sample = Sample(
                        id=str(uuid.uuid4()),
                        tenant_id=tenant.id,
                        order_item_id=first_item.id,
                        barcode=case["sample_barcode"],
                        specimen_type=case["specimen"],
                        container_type=case["tube_color"],
                        status=case["sample_status"],
                        collected_at=case["sample_collection_time"],
                        collected_by=phleb_user.id if phleb_user else None,
                        received_at=case["sample_received_time"],
                        received_by=path_user.id if path_user else None,
                        accepted_at=case["sample_received_time"],
                    )
                    session.add(sample)
                    session.flush()

                    # Result & Result Values
                    if case["results"]:
                        res = Result(
                            id=str(uuid.uuid4()),
                            tenant_id=tenant.id,
                            order_item_id=first_item.id,
                            sample_id=sample.id,
                            status="released" if case["report_status"] == "released" else "entered",
                            entered_at=case["sample_received_time"],
                            approved_at=case["report_generation_time"],
                            approved_by=path_user.id if path_user else None,
                        )
                        session.add(res)
                        session.flush()

                        for rv in case["results"]:
                            session.add(ResultValue(
                                id=str(uuid.uuid4()),
                                result_id=res.id,
                                analyte_code=rv["analyte"],
                                raw_value=rv["raw"],
                                numeric_value=Decimal(str(rv["num"])),
                                abnormal_flag=rv["flag"],
                                unit=rv["unit"],
                            ))

                        # Report with Report Generation Time
                        if case["report_no"]:
                            rep = Report(
                                id=str(uuid.uuid4()),
                                tenant_id=tenant.id,
                                patient_id=p_obj.id,
                                result_id=res.id,
                                report_no=case["report_no"],
                                status=case["report_status"],
                                created_at=case["report_generation_time"] or now,
                                released_at=case["report_generation_time"],
                            )
                            session.add(rep)

                # Invoice
                inv = Invoice(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant.id,
                    branch_id=branch.id,
                    patient_id=p_obj.id,
                    order_id=order.id,
                    invoice_no=f"INV-{case['order_no']}",
                    currency="INR",
                    subtotal=case["total_amount"],
                    grand_total=case["total_amount"],
                    paid_amount=case["total_amount"],
                    status="paid",
                )
                session.add(inv)

        # 7. Blood Bank Units Inventory
        blood_groups = [
            ("A+", 12, "Normal"),
            ("A-", 4, "Low"),
            ("B+", 15, "Normal"),
            ("B-", 3, "Low"),
            ("O+", 20, "Normal"),
            ("O-", 5, "Critical"),
            ("AB+", 6, "Normal"),
            ("AB-", 2, "Low"),
        ]
        # Seed demo donor
        donor = session.query(Donor).filter_by(tenant_id=tenant.id, donor_no="DNR-0001").first()
        if not donor:
            donor = Donor(
                id=str(uuid.uuid4()),
                tenant_id=tenant.id,
                donor_no="DNR-0001",
                first_name="Vikram",
                last_name="Malhotra",
                blood_group="O+",
                status="active",
            )
            session.add(donor)
            session.flush()

        donation = session.query(Donation).filter_by(tenant_id=tenant.id, donation_no="DON-0001").first()
        if not donation and donor:
            donation = Donation(
                id=str(uuid.uuid4()),
                tenant_id=tenant.id,
                donor_id=donor.id,
                donation_no="DON-0001",
                donation_type="whole_blood",
                volume_ml=450,
                status="screened",
            )
            session.add(donation)
            session.flush()

        session.commit()
    print("[SUCCESS] Fully initialized and populated Aarozi Healthcare database with:")
    print(" - Tests, Price Lists, Patients, Orders")
    print(" - Samples with Sample Collection Time (collected_at)")
    print(" - Clinical Results and Diagnostic Reports with Report Generation Time (released_at / created_at)")
    print(" - Invoices, Payments, and Blood Bank Inventory.")


if __name__ == "__main__":
    seed_database()

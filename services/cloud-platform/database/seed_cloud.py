"""One-click seed script for Aarozi Healthcare Hosted Cloud Platform Database.

Usage:
  DATABASE_URL="postgresql://user:pass@ep-host.neon.tech/neondb" python seed_cloud.py
"""

from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# Add services/cloud-platform to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models import (
    Base,
    CmsBlogPost,
    DesktopRelease,
    IssuedLicense,
    PaymentTransaction,
    PlatformAdmin,
    SubscriptionPlan,
    TenantLaboratory,
)

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_pw(pw: str) -> str:
    return pwd_context.hash(pw)


def seed_cloud():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        # Default to local sqlite for dev testing if no remote DB specified
        dev_file = Path(__file__).resolve().parent / "cloud_dev.db"
        db_url = f"sqlite:///{dev_file}"

    print(f"[*] Initializing Cloud Platform Database: {db_url}")
    engine = create_engine(db_url, connect_args={"check_same_thread": False} if "sqlite" in db_url else {})
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        # 1. Super Admin
        admin_email = "superadmin@aarozi.in"
        admin = session.query(PlatformAdmin).filter_by(email=admin_email).first()
        if not admin:
            admin = PlatformAdmin(
                email=admin_email,
                hashed_password=hash_pw("Admin@12345"),
                full_name="Super Administrator",
                role="SUPER_ADMIN",
                is_active=True,
            )
            session.add(admin)
            print(f"[+] Created Super Admin: {admin_email}")

        # Secondary admin
        sec_email = "admin@aarozi.com"
        sec_admin = session.query(PlatformAdmin).filter_by(email=sec_email).first()
        if not sec_admin:
            sec_admin = PlatformAdmin(
                email=sec_email,
                hashed_password=hash_pw("Admin@12345"),
                full_name="Platform Operations Head",
                role="SUPER_ADMIN",
                is_active=True,
            )
            session.add(sec_admin)

        # 2. Subscription Plans
        plans_data = [
            {
                "code": "MONTHLY_STARTER",
                "name": "Starter Monthly",
                "billing_cycle": "monthly",
                "base_price_inr": 1499.00,
                "duration_days": 30,
                "grace_days": 7,
                "max_workstations": 3,
                "is_lifetime": False,
                "features_json": [
                    "Complete Pathology & Biochemistry",
                    "POS Billing & Cashier Receipts",
                    "Barcode Specimen Label Printing",
                    "Direct WhatsApp Report Dispatch",
                    "Up to 3 LAN Workstations",
                ],
            },
            {
                "code": "YEARLY_PRO",
                "name": "Professional Yearly",
                "billing_cycle": "annual",
                "base_price_inr": 14999.00,
                "duration_days": 365,
                "grace_days": 30,
                "max_workstations": 15,
                "is_lifetime": False,
                "features_json": [
                    "All Starter Features Included",
                    "Blood Bank & Inventory Management",
                    "Automated Mindray/Cobas Analyzer Interfacing",
                    "Google Drive Automated Backups",
                    "NABL Levey-Jennings QC Graphs",
                    "15 LAN Workstations",
                    "1 Year Software Updates & Support",
                ],
            },
            {
                "code": "ENTERPRISE_MULTI",
                "name": "Multi-Branch Enterprise",
                "billing_cycle": "annual",
                "base_price_inr": 29999.00,
                "duration_days": 365,
                "grace_days": 30,
                "max_workstations": 35,
                "is_lifetime": False,
                "features_json": [
                    "All Professional Features Included",
                    "Multi-Branch Central Reporting",
                    "Radiology (X-Ray / USG) Reporting Hub",
                    "Corporate B2B & Referral Doctor Portal",
                    "Priority 24/7 Remote Desk Setup",
                    "Unlimited LAN Workstations",
                ],
            },
            {
                "code": "LIFETIME_COMMERCIAL",
                "name": "Lifetime Perpetual License",
                "billing_cycle": "one_time",
                "base_price_inr": 39999.00,
                "duration_days": 36500,
                "grace_days": 0,
                "max_workstations": 50,
                "is_lifetime": True,
                "features_json": [
                    "All Enterprise Features Included",
                    "Perpetual Software License (Never Expires)",
                    "Zero Recurring Subscription Fees",
                    "Hardware Locked Anti-Theft Cryptography",
                    "Free Updates for Major Version (v2.x)",
                    "Direct Developer Access & Support",
                ],
            },
        ]

        for p_info in plans_data:
            existing_p = session.query(SubscriptionPlan).filter_by(code=p_info["code"]).first()
            if not existing_p:
                p_obj = SubscriptionPlan(**p_info)
                session.add(p_obj)
                print(f"[+] Added Plan: {p_info['name']} (₹{p_info['base_price_inr']})")

        session.flush()

        # 3. Sample Diagnostic Laboratories
        labs_data = [
            {
                "lab_name": "Apex Diagnostic & Imaging Centre",
                "owner_name": "Dr. Ramesh Sharma, MD (Path)",
                "email": "dr.sharma@apexlab.in",
                "phone": "+91 98765 43210",
                "city": "Lucknow",
                "state": "Uttar Pradesh",
                "gstin": "09AAACA1234D1Z5",
                "status": "ACTIVE",
                "plan_code": "YEARLY_PRO",
                "hardware_fingerprint": "HW-89F4-A012-78BC",
            },
            {
                "lab_name": "Metro Pathology Care",
                "owner_name": "Dr. Sneha Verma",
                "email": "contact@metropath.org",
                "phone": "+91 98111 22334",
                "city": "Jaipur",
                "state": "Rajasthan",
                "gstin": "08BBBCB2345E1Z6",
                "status": "ACTIVE",
                "plan_code": "LIFETIME_COMMERCIAL",
                "hardware_fingerprint": "HW-CC91-45A0-11EF",
            },
            {
                "lab_name": "Sunrise Clinical Diagnostics",
                "owner_name": "Dr. Vikram Patel",
                "email": "vikram@sunriselab.in",
                "phone": "+91 99887 76655",
                "city": "Ahmedabad",
                "state": "Gujarat",
                "gstin": "24CCCCD3456F1Z7",
                "status": "TRIAL",
                "plan_code": "MONTHLY_STARTER",
                "hardware_fingerprint": "HW-FA33-12BC-9901",
            },
        ]

        for l_info in labs_data:
            existing_l = session.query(TenantLaboratory).filter_by(email=l_info["email"]).first()
            if not existing_l:
                l_obj = TenantLaboratory(**l_info)
                session.add(l_obj)
                session.flush()

                # Issue license for active labs
                now = datetime.utcnow()
                lic_key = f"LIC-PROD-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
                lic = IssuedLicense(
                    license_key=lic_key,
                    lab_id=l_obj.id,
                    plan_code=l_obj.plan_code,
                    valid_from=now - timedelta(days=5),
                    valid_to=now + timedelta(days=360),
                    grace_until=now + timedelta(days=390),
                    hardware_fingerprint=l_obj.hardware_fingerprint,
                    signature_hex="353bc5669a736869b1e3105eb171ab83e2ad03c9df0049366102be6085b3426ec421638e4301803d4268405bb16dc87d32241e8da75cae5f94550f8afcaf5c02",
                    license_payload_json={
                        "license_id": lic_key,
                        "lab_name": l_obj.lab_name,
                        "plan": l_obj.plan_code,
                        "workstations": 15,
                    },
                    status="ACTIVE",
                )
                session.add(lic)
                print(f"[+] Onboarded Lab: {l_obj.lab_name} with License {lic_key}")

        # 4. Windows Desktop Release
        rel = session.query(DesktopRelease).filter_by(version="v2.4.0").first()
        if not rel:
            rel = DesktopRelease(
                version="v2.4.0",
                release_title="Aarozi Healthcare LIS — Offline Master Edition v2.4.0",
                release_notes="Features automated Mindray/Cobas analyzer interfacing, WhatsApp report dispatch, thermal barcode label printing, and NABL Levey-Jennings QC compliance.",
                download_url="/downloads/Aarozi-LIS-Setup-v2.4.0.exe",
                file_size_mb=84.50,
                sha256_checksum="5a5a7291adae8c58ecc861841ad64af8a6c972a737d65c725d0e6f319ef85fb8",
                is_latest=True,
                is_mandatory=False,
            )
            session.add(rel)
            print("[+] Seeded Windows Release: v2.4.0")

        # 5. CMS Blog Posts
        posts_data = [
            {
                "title": "Why Offline-First Architecture is Critical for Pathology Labs in India",
                "slug": "offline-first-pathology-lims-india",
                "excerpt": "Broadband outages and cloud latency cost Indian diagnostic labs thousands daily. Here is why local LAN architecture guarantees 100% uninterrupted operations.",
                "content_markdown": "In tier-2 and tier-3 Indian cities, intermittent internet connectivity is common. When a cloud-only LIS goes down, front desk billing halts, tube barcodes cannot print, and analyzers stall. An offline-first LIS with encrypted local database guarantees uninterrupted zero-lag operations.",
                "category": "Technology",
                "read_time_minutes": 5,
            },
            {
                "title": "NABL ISO 15189:2022 Compliance Guide for Small and Medium Diagnostics",
                "slug": "nabl-iso-15189-compliance-checklist",
                "excerpt": "A complete practical roadmap for obtaining and maintaining NABL accreditation using automated Levey-Jennings charts and multi-level Westgard rules.",
                "content_markdown": "Maintaining daily Levey-Jennings control charts and calibrating analyzers can be tedious on paper. Using an automated QC module enables technicians to flag 1-2s and 1-3s violations immediately before releasing clinical patient reports.",
                "category": "NABL Compliance",
                "read_time_minutes": 7,
            },
            {
                "title": "Eliminate Report Distribution Bottlenecks with WhatsApp Automation",
                "slug": "whatsapp-patient-report-dispatch",
                "excerpt": "How diagnostic centres cut printing costs by 65% and increase patient satisfaction by delivering QR-verified digital PDF reports straight to WhatsApp.",
                "content_markdown": "Patients prefer instant smartphone delivery. Integrating WhatsApp direct API dispatch sends password-protected diagnostic reports in seconds, complete with QR code tamper verification.",
                "category": "Business",
                "read_time_minutes": 4,
            },
        ]

        for post_info in posts_data:
            existing_post = session.query(CmsBlogPost).filter_by(slug=post_info["slug"]).first()
            if not existing_post:
                post_obj = CmsBlogPost(**post_info)
                session.add(post_obj)
                print(f"[+] Added Blog Post: {post_info['title']}")

        session.commit()
        print("[✓] Cloud Platform Database successfully seeded!")


if __name__ == "__main__":
    seed_cloud()


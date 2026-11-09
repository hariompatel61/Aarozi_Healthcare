"""Seed script to populate referral partners, referral rules, invoice items, and relational links between Patients, Invoices, and Referral Partners."""
import sqlite3
import uuid
import datetime

DB_PATH = "apps/api/dev_aarozi.db"

def seed():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    
    # Check if specialty column exists
    cols = [c[1] for c in cur.execute("PRAGMA table_info(referral_partners)").fetchall()]
    if "specialty" not in cols:
        print("[*] Adding specialty column to referral_partners")
        cur.execute("ALTER TABLE referral_partners ADD COLUMN specialty VARCHAR(100)")
        con.commit()

    tenant_id = "d0cab5f3-45ff-4943-b0c3-dbd67a6b228a"
    branch_id = "e445a313-1025-4323-9cd9-712895eee9ff"
    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # 1. Seed Referral Partners (Doctors and Hospitals)
    doctors = [
        {
            "id": "ref-dr-sharma",
            "name": "Dr. Rajesh Sharma, MD",
            "partner_type": "doctor",
            "specialty": "Cardiologist",
            "phone": "+91 98112 34567",
            "email": "dr.sharma@cardio.med",
            "comm_pct": 15.0,
        },
        {
            "id": "ref-dr-mehta",
            "name": "Dr. Sunita Mehta, MBBS, DGO",
            "partner_type": "doctor",
            "specialty": "Gynecologist & Obstetrician",
            "phone": "+91 98223 45678",
            "email": "dr.mehta@womensclinic.in",
            "comm_pct": 20.0,
        },
        {
            "id": "ref-dr-verma",
            "name": "Dr. Anand Verma, MD",
            "partner_type": "doctor",
            "specialty": "Internal Medicine / Diabetologist",
            "phone": "+91 98334 56789",
            "email": "dr.verma@citymed.org",
            "comm_pct": 12.0,
        },
        {
            "id": "ref-hosp-lifecare",
            "name": "Lifecare Multispecialty Hospital",
            "partner_type": "hospital",
            "specialty": "Hospital & Emergency Care",
            "phone": "+91 11 2548 9900",
            "email": "outreach@lifecarehospitals.in",
            "comm_pct": 10.0,
        },
        {
            "id": "ref-dr-desai",
            "name": "Dr. Priya Desai, MS",
            "partner_type": "doctor",
            "specialty": "General & Laparoscopic Surgeon",
            "phone": "+91 98445 67890",
            "email": "dr.priyadesai@surgery.net",
            "comm_pct": 15.0,
        },
        {
            "id": "ref-coll-apex",
            "name": "Apex Care Sample Collection Centre",
            "partner_type": "collection_centre",
            "specialty": "Peripheral Diagnostic Outreach",
            "phone": "+91 11 4152 3344",
            "email": "apex.intake@aarozi.local",
            "comm_pct": 8.0,
        },
    ]

    for d in doctors:
        existing = cur.execute("SELECT id FROM referral_partners WHERE id = ? OR name = ?", (d["id"], d["name"])).fetchone()
        if not existing:
            cur.execute("""
                INSERT INTO referral_partners (id, tenant_id, partner_type, name, specialty, phone, email, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?)
            """, (d["id"], tenant_id, d["partner_type"], d["name"], d["specialty"], d["phone"], d["email"], now_str))
            
            # Insert commission rule
            rule_id = f"rule-{d['id']}"
            cur.execute("""
                INSERT INTO referral_rules (id, tenant_id, partner_id, scope_type, effective_from, patient_discount_pct, commission_pct, commission_fixed, priority, status, created_at)
                VALUES (?, ?, ?, 'all', ?, 0.0, ?, 0.0, 100, 'active', ?)
            """, (rule_id, tenant_id, d["id"], now_str, d["comm_pct"], now_str))

    con.commit()
    print("[*] Seeded 6 referral partners and rules.")

    # 2. Get existing patients
    patients = cur.execute("SELECT id, patient_no, first_name, last_name FROM patients").fetchall()
    print(f"[*] Found {len(patients)} patients in database.")

    # 3. Associate orders and invoices with referral doctors
    orders = cur.execute("SELECT id, patient_id FROM orders").fetchall()
    invoices = cur.execute("SELECT id, patient_id, order_id, grand_total FROM invoices").fetchall()

    for idx, ord_row in enumerate(orders):
        doc = doctors[idx % len(doctors)]
        cur.execute("UPDATE orders SET referral_partner_id = ? WHERE id = ?", (doc["id"], ord_row[0]))

    for idx, inv_row in enumerate(invoices):
        doc = doctors[idx % len(doctors)]
        cur.execute("UPDATE invoices SET referral_partner_id = ? WHERE id = ?", (doc["id"], inv_row[0]))

    con.commit()
    print("[*] Linked orders and invoices with referral partners.")

    # 4. Populate invoice items if missing
    inv_items_count = cur.execute("SELECT COUNT(*) FROM invoice_items").fetchone()[0]
    if inv_items_count == 0:
        print("[*] Populating invoice_items for existing invoices")
        default_items = [
            ("CBC Complete Blood Count", 350.0),
            ("LFT Liver Function Test", 750.0),
            ("KFT Kidney Function Test", 650.0),
            ("Thyroid Profile T3 T4 TSH", 550.0),
            ("Lipid Profile Lipid Panel", 500.0),
        ]
        
        for inv_row in invoices:
            inv_id = inv_row[0]
            amt = inv_row[3] or 850.0
            item_desc, item_price = default_items[hash(inv_id) % len(default_items)]
            item_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO invoice_items (id, tenant_id, invoice_id, order_item_id, item_type, description, qty, unit_price, discount_pct, discount_amount, tax_rate_pct, tax_amount, line_total, created_at)
                VALUES (?, ?, ?, NULL, 'test', ?, 1.0, ?, 0.0, 0.0, 0.0, 0.0, ?, ?)
            """, (item_id, tenant_id, inv_id, item_desc, item_price, amt, now_str))

        con.commit()
        print("[*] Populated invoice_items.")

    # 5. Populate commission ledger
    cur.execute("DELETE FROM commission_ledger")
    for inv_row in invoices:
        inv_id = inv_row[0]
        amt = float(inv_row[3] or 850.0)
        partner_id = cur.execute("SELECT referral_partner_id FROM invoices WHERE id = ?", (inv_id,)).fetchone()[0]
        if partner_id:
            comm_pct = 15.0
            for d in doctors:
                if d["id"] == partner_id:
                    comm_pct = d["comm_pct"]
                    break
            comm_amt = round(amt * (comm_pct / 100.0), 2)
            cur.execute("""
                INSERT INTO commission_ledger (id, tenant_id, referral_partner_id, invoice_id, amount, status, calculated_at, created_at)
                VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)
            """, (str(uuid.uuid4()), tenant_id, partner_id, inv_id, comm_amt, now_str, now_str))

    con.commit()
    print("[*] Populated commission ledger.")
    con.close()
    print("[*] Seeding and database relations completed successfully.")

if __name__ == "__main__":
    seed()

# Aarozi Healthcare — Yearly Subscription Expiry & Renewal Architecture

---

## 1. Expiration Policy & Clinical Data Preservation

When a 365-day yearly subscription reaches its end date:

1. **30-Day Soft Grace Period:**
   - For 30 days after the nominal expiration date, all clinical, registration, billing, and analyzer workflows continue **100% unimpeded**.
   - A non-blocking renewal reminder banner is displayed on the dashboard.
2. **Post-Grace Restricted Mode:**
   - If unpaid after Day 30 of grace, new patient registrations and billings are paused.
   - **ZERO DATA LOSS:** All historical patient records, test results, doctor reports, and accounting ledgers remain permanently searchable, viewable, and printable.
   - Local database exports, Google Drive backups, and license imports remain fully operational.

---

## 2. 1-Click Renewal Workflow (No Reinstallation)

The customer never needs to reinstall software or migrate data upon renewal:

```
[ Lab Owner Portal ] ──► [ 1-Click Pay ₹14,999 + GST ] ──► [ Verified Razorpay Webhook ]
                                                                      │
                                                                      ▼
[ Local Lab Workstation ] ◄── [ Import New .lic ] ◄── [ Signed Ed25519 Extension ]
```

1. Log into the Customer Portal &rarr; Click **Renew Subscription**.
2. Complete payment via UPI, Credit/Debit Card, or Netbanking.
3. Razorpay webhook confirms the transaction.
4. The system signs an updated Ed25519 license extending `valid_to` by another 365 days while **preserving the exact same Installation ID and Tenant ID**.
5. Download the new `.lic` file and import it under **Settings &rarr; System Licensing**.
6. Full active commercial status is restored instantly!


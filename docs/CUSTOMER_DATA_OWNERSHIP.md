# Aarozi Healthcare — Customer Clinical Data Ownership & Zero-Central-Hosting Manifesto

**Foundational Architectural Principle:**  
*The central Aarozi Healthcare platform shall NEVER store, ingest, host, or inspect any diagnostic laboratory's patient database, clinical test results, doctor notes, or medical attachments.*

---

## 1. Why Zero-Central-Patient-Hosting?

1. **Vendor Financial Sustainability (No Storage or Egress Costs for 10,000+ Labs):**
   - If 10,000 diagnostic centers process 100 patients/day, that equates to 1,000,000 patient records and 1,000,000 generated PDF reports daily.
   - Hosting that volume centrally would require petabytes of redundant storage, multi-zone database clusters, and millions in monthly AWS/GCP bills.
   - By running on the **laboratory's own master PC**, your cloud operational cost for 10,000 laboratories stays under **₹25,000 / month total**!

2. **Legal & Regulatory Immunity (DPDP Act 2023 & Indian Healthcare Standards):**
   - The laboratory owner is the legal **Data Fiduciary**.
   - Aarozi Healthcare operates purely as the **Software Vendor**.
   - Because patient data never touches Aarozi servers, Aarozi avoids liabilities associated with third-party medical data breaches, cross-tenant data leaks, or regulatory inspection of central patient repositories.

3. **Total Laboratory Sovereignty & Offline Resilience:**
   - Indian diagnostic clinics often experience broadband dropouts or power outages.
   - Core operations (sample registration, barcoding, analyzer feeds, emergency blood cross-matching) never pause because the local server is 100% self-sufficient.

---

## 2. Customer-Owned Cloud Backup via Personal Google Drive

Rather than paying the vendor for expensive cloud storage, every laboratory owner connects **their own Google account**:
- Diagnostic labs utilize the free 15 GB quota included with every standard Google account (or their clinic's Google Workspace account).
- A compressed, AES-256 encrypted SQLite snapshot is ~40 MB. 15 GB of storage comfortably holds **over 350 full daily database backups**!
- Access is restricted via least-privilege OAuth scope: `https://www.googleapis.com/auth/drive.file`. Aarozi only sees the backup folder it creates; it can never view the customer's personal Drive files.


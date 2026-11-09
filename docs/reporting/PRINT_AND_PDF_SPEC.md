# Print and PDF Rendering Specification - Aarozi Healthcare

**Author**: Senior Software Architect & Clinical Systems Engineer  
**Scope**: High-fidelity A4 PDF generation, local printer integration, browser print stylesheets, and offline rendering specifications.

---

## 1. Multi-Page Layout & Continuation Rules

Diagnostic reports frequently span multiple pages (e.g., extensive lipid/cardiac panels, comprehensive hematology, biopsy narratives). The PDF engine enforces strict pagination rules:

1. **Page Numbering**:
   - Every page displays unambiguous pagination: `Page X of Y` (e.g., `Page 1 of 3`).
   - The total page count $Y$ is dynamically computed after full layout layout tree resolution.
2. **Repeating Continuation Headers**:
   - On Page 2 and subsequent pages, a compact continuation header automatically renders:
     `Patient: Jane Doe (UHID: UH2026-0042) | Accession: ACC-8921 | Page 2 of 3`
   - This ensures loose pages separated in hospital wards can always be attributed to the correct patient and sample.
3. **Repeating Table Headers & Orphan Prevention**:
   - If a result table splits across page boundaries, table column headers (`Investigation`, `Observed Value`, `Unit`, `Biological Reference Interval`) are automatically repeated at the top of the next page.
   - Individual result rows are never split across pages. A minimum orphan threshold of 3 lines is enforced before breaking to the next page.
4. **End of Report Sentinel**:
   - The final page displays an explicit termination marker: `*** END OF REPORT ***`.
   - Prevents patients or clinicians from suspecting missing pages.

---

## 2. Watermarking, QR Code Authenticity & Digital Signatures

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              [ LAB LOGO & NAME ]                            │
│ ─────────────────────────────────────────────────────────────────────────── │
│ Patient: John Smith (45Y / M)               Accession: ACC-1092             │
│ Ref By:  Dr. R. Sharma, MD                  Collected: 15-Oct-2026 09:30    │
│ ─────────────────────────────────────────────────────────────────────────── │
│                              [ WATERMARK: DRAFT ]                           │
│   TEST NAME              RESULT       UNIT      REFERENCE INTERVAL   FLAG   │
│   Hemoglobin             14.2         g/dL      13.0 - 17.0                 │
│   Total Leukocyte Count  11,500       /cumm     4,000 - 10,000        H     │
│   Platelet Count         220,000      /cumm     150,000 - 450,000           │
│ ─────────────────────────────────────────────────────────────────────────── │
│ Comment: Leukocytosis noted. Please correlate clinically.                   │
│                                                                             │
│ [ QR CODE ]             [ VERIFIED DIGITAL STAMP ]                          │
│ Scan to Verify          Dr. Anita Roy, MD (Pathology)                       │
│ Authenticity            Reg. No: MCI-2014-9982                              │
│ ─────────────────────────────────────────────────────────────────────────── │
│ Page 1 of 1                     *** END OF REPORT ***                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

1. **Watermark Control**:
   - *Draft / Preview Reports*: Large, semi-transparent diagonal watermark (`DRAFT - NOT FOR CLINICAL USE` at $45^\circ$, `#E2E8F0` opacity 0.25).
   - *Approved / Released Reports*: Watermark is removed; official laboratory letterhead and digital signature stamps become active.
2. **Instant QR Code Authenticity Verification**:
   - Each released report embeds a cryptographic QR code in the signature block.
   - Scanning the QR code resolves to the local LAN server or secure web portal verifying:
     - Report Hash (SHA-256)
     - Patient UHID & Accession Number
     - Pathologist Name & Approval Timestamp
   - Prevents fraudulent paper report tampering.
3. **Digital Signature Integration**:
   - Signatures are stored as secure, encrypted image assets linked to authorized pathologist user IDs.
   - When a pathologist approves a report, their cryptographic hash and verified stamp are embedded directly into the generated PDF.

---

## 3. Font Embedding & Bilingual Typography (English & Hindi)

- **Font Subsetting & Embedding**:
  - All fonts (e.g., Inter, Noto Sans Devanagari) are fully embedded inside the PDF file.
  - Guarantees identical visual rendering across any PDF reader, mobile device, or operating system without relying on client-installed system fonts.
- **Hindi / Regional Language Support**:
  - Supports Hindi and regional language headers, instructions, and patient-facing notes (e.g., *"रिपोर्ट की व्याख्या के लिए कृपया अपने चिकित्सक से परामर्श लें"*).
  - Uses UTF-8 encoding throughout the rendering pipeline.

---

## 4. Local Offline Rendering & Zero Cloud Dependency

- **Offline-First Architecture**:
  - The PDF rendering service (`pdf_service.py` in `apps/api`) runs entirely on the local LAN server.
  - Operates with 100% fidelity even when the internet is completely disconnected.
  - Assets (logos, signatures, QR generation libraries, fonts) are loaded from local disk storage (`apps/api/static/` or local database BLOBs).
- **Printer Compatibility**:
  - Standard A4 Laser / Inkjet Printers: Direct PDF print stream.
  - Cashier Receipt Printers: 80mm / 58mm ESC/POS thermal receipt formatting for billing counters.

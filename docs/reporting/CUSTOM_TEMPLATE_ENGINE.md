# Custom Report Template Engine - Aarozi Healthcare

**Author**: Senior Healthcare Software Architect & Senior Frontend Engineer  
**Scope**: Specifications and design for the visual, block-based, data-driven report template engine.

---

## 1. Architectural Philosophy: Visual Flexibility vs. Clinical Invariants

A critical design requirement of Aarozi Healthcare is allowing every diagnostic laboratory to tailor its visual report presentation (letterhead, typography, column widths, laboratory disclaimers) while strictly protecting the integrity of underlying clinical facts:

```
┌──────────────────────────────────────────────┬──────────────────────────────────────────────┐
│  Customizable by the Laboratory (Visual)     │  Controlled by Clinical Invariant (System)   │
├──────────────────────────────────────────────┼──────────────────────────────────────────────┤
│ • Laboratory Logo, Address, NABL/ISO badges  │ • Measured laboratory result values          │
│ • Header, Footer, and Margins                │ • Approved Biological Reference Intervals    │
│ • Section Ordering & Column Alignment        │ • Analytical Methodology and Specimen Type   │
│ • Font Sizes, Colors, and Table Borders      │ • Result Flags ('L', 'H', 'LL', 'HH')        │
│ • Approved Observation & Disclaimer Text     │ • Pathologist Approval & Digital Signatures  │
│ • Repeating Page Headers & Page Numbers      │ • Exact Timestamp and Immutable Audit Trail  │
└──────────────────────────────────────────────┴──────────────────────────────────────────────┘
```

---

## 2. Template Scoping & Deterministic Selection Hierarchy

Templates are resolved hierarchically with strict tenant isolation:

1. **Test / Profile Specific Template**: Custom layout tailored for a specific complex investigation (e.g., Histopathology Report, Serum Electrophoresis curve, Karyotyping).
2. **Department Template**: Layout for a discipline (e.g., Biochemistry vs. Microbiology culture plates).
3. **Branch Template**: Location-specific branding for a satellite laboratory.
4. **Tenant Default Template**: Standard laboratory letterhead for the organization.
5. **Global System Starter Template**: Fallback starter template provided by Aarozi core.

*Security Invariant*: A tenant can NEVER query, view, or inherit private templates belonging to another tenant.

---

## 3. Visual Designer Layout Blocks & Controlled JSON Schema

Report templates are stored as structured JSON layouts in `report_template_versions.schema_json` (Alembic migration `20241013_18_report_templates.py`). Arbitrary executable JavaScript and raw unrestricted HTML are strictly prohibited to prevent template injection attacks.

### Standard Supported Layout Blocks
1. `header_branding`: Laboratory logo, hospital name, registration number, contact info, accreditation badges (NABL, CAP, ISO 15189).
2. `patient_demographics`: UHID barcode, Patient Name, Age, Sex, Referring Doctor, Collection Center, Ward/Bed number.
3. `order_accession`: Lab Accession Number, Barcode, Sample Collection Time, Sample Received Time, Report Released Time.
4. `result_table`: Dynamic parameters, test names, measured values, units, biological reference intervals, previous result (delta comparison), method name.
5. `clinical_comments`: Pathologist interpretive remarks, abnormal findings advisory, clinical recommendations.
6. `signatures_block`: Pathologist name, qualification (MD/DCP), registration number, verified digital signature stamp, QR code verification badge.
7. `footer_disclaimer`: Repeating continuation notice ("Report continued on next page..."), legal disclaimer, end of report marker ("*** END OF REPORT ***").

### Validated JSON Schema Specification
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "AaroziReportTemplateSchema",
  "type": "object",
  "required": ["version", "page", "blocks"],
  "properties": {
    "version": { "type": "string", "enum": ["1.0"] },
    "page": {
      "type": "object",
      "required": ["size", "orientation", "margins"],
      "properties": {
        "size": { "type": "string", "enum": ["A4", "Letter"] },
        "orientation": { "type": "string", "enum": ["portrait", "landscape"] },
        "margins": {
          "type": "object",
          "properties": {
            "top_mm": { "type": "number", "default": 15 },
            "bottom_mm": { "type": "number", "default": 15 },
            "left_mm": { "type": "number", "default": 15 },
            "right_mm": { "type": "number", "default": 15 }
          }
        }
      }
    },
    "blocks": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "type", "visible"],
        "properties": {
          "id": { "type": "string" },
          "type": {
            "type": "string",
            "enum": [
              "header_branding",
              "patient_demographics",
              "order_accession",
              "result_table",
              "clinical_comments",
              "signatures_block",
              "footer_disclaimer"
            ]
          },
          "visible": { "type": "boolean", "default": true },
          "config": { "type": "object" }
        }
      }
    }
  }
}
```

---

## 4. Immutable Release Locking & Amendment Tracking

1. **Historical Immutability**:
   - When a report is approved and released by a pathologist, the exact `template_version_id` and test reference definitions are recorded in the `reports` table.
   - Future edits, redesigns, or deletions of that template will NOT affect already generated and released reports.
2. **Clinical Report Amendments**:
   - Released reports cannot be silently edited.
   - If a result value requires correction (e.g., after sample dilution or re-testing):
     - An amendment workflow creates a new record in `reports` with an incremented `version_number` (e.g., `v2`).
     - The previous version is preserved with status `amended`.
     - The amendment must cite the authorized pathologist and mandatory clinical reason for amendment.

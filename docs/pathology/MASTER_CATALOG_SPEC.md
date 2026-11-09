# Master Pathology Catalog Specification - Aarozi Healthcare

**Author**: LIS/LIMS Domain Expert & Clinical Data Quality Engineer  
**Scope**: Definitive specification for 1,000+ distinct clinical investigations, schema mapping, and reference range data governance.

---

## 1. Disciplines, Categories and Clinical Coverage

The master catalog provides canonical test definitions across 20 primary laboratory disciplines. Each test is uniquely identified and distinct from profiles, packages, and method variations:

| # | Laboratory Discipline | Representative Canonical Investigations | Specimen Types | Typical Container |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **Hematology & CBC** | Complete Blood Count (18 params), Peripheral Smear, ESR, Absolute Eosinophil Count, Reticulocyte Count, Osmotic Fragility | Whole Blood | K2/K3 EDTA (Lavender) |
| **2** | **Coagulation** | Prothrombin Time (PT/INR), APTT, Fibrinogen, D-Dimer, Thrombin Time, Factor VIII/IX Assay, Protein C & S | Citrated Plasma | 3.2% Sodium Citrate (Light Blue) |
| **3** | **Clinical Biochemistry** | Blood Glucose (Fasting/PP/Random), HbA1c, Serum Electrolytes (Na, K, Cl, iCa), Serum Osmolality, Arterial Blood Gas (ABG) | Serum / Heparin Plasma | Clot Activator / SST (Yellow/Red), Heparin (Green) |
| **4** | **Liver & Renal Function** | Bilirubin (Total/Direct/Indirect), SGOT/AST, SGPT/ALT, Alkaline Phosphatase, GGT, Total Protein, Albumin, Urea, BUN, Creatinine, Uric Acid, eGFR | Serum | SST Gel Separator (Yellow) |
| **5** | **Lipid & Cardiac Markers** | Total Cholesterol, Triglycerides, HDL, LDL, VLDL, Troponin I/T (High Sensitivity), CK-MB, CPK, NT-proBNP, Myoglobin, Homocysteine | Serum / Heparin Plasma | SST Gel (Yellow), Heparin (Green) |
| **6** | **Diabetes & Metabolic** | Insulin (Fasting/PP), C-Peptide, HOMA-IR, Fructosamine, Microalbumin (Urinary), Ketone Bodies | Serum / Fluoride Plasma | Sodium Fluoride (Grey), SST |
| **7** | **Thyroid & Endocrine** | Total T3, Total T4, Free T3, Free T4, TSH (Ultra-sensitive), Cortisol, Prolactin, Testosterone, ACTH, Growth Hormone, PTH | Serum | SST Gel Separator (Yellow) |
| **8** | **Immunology & Serology** | Widal, Dengue NS1/IgM/IgG, Chikungunya, Typhidot, ANA (IF/ELISA), dsDNA, RA Factor, ASO Titer, CRP (Quantitative), hs-CRP, Procalcitonin | Serum | Clot Activator (Red/Yellow) |
| **9** | **Infectious Disease Testing** | HIV 1&2 (4th Gen ELISA/CLIA), HBsAg, HCV, VDRL/RPR, Malaria Antigen (Pv/Pf), Scrub Typhus IgM, Leptospira IgM | Serum / Whole Blood | Clot Activator (Red/Yellow), EDTA |
| **10** | **Urinalysis & Body Fluids** | Urine Routine & Microscopy (14 params), 24-hr Urinary Protein, Pleural Fluid Analysis, Ascitic Fluid, Synovial Fluid Analysis, CSF Routine | Urine / Body Fluids | Sterile Urine Container, Plain Sterile Tube |
| **11** | **Stool & Parasitology** | Stool Routine & Microscopy, Occult Blood (FOBT), Reducing Substances, Stool Antigen for Helicobacter pylori, Cryptosporidium | Stool Specimen | Wide-mouth Clean Container |
| **12** | **Microbiology & Culture** | Blood Culture & Sensitivity, Urine Culture, Sputum C&S, Pus Culture, Swab Culture, Fungal KOH Mount, Gram Stain, AFB Stain | Various | Blood Culture Bottle, Sterile Swabs, Sterile Container |
| **13** | **Histopathology & Cytology** | Biopsy (Small/Medium/Large), PAP Smear, FNAC, Sputum Cytology, Fluid Cytology, Cell Block Preparation | Tissue / Smear | 10% Neutral Buffered Formalin, Cyto-fixative |
| **14** | **Molecular Diagnostics & PCR** | TB PCR (CBNAAT/GeneXpert), Hepatitis B DNA Quantitative, Hepatitis C RNA Quantitative, HPV High-Risk Screening, HLA-B27 | Whole Blood / Sputum / Swabs | EDTA (Lavender), Viral Transport Medium (VTM) |
| **15** | **Tumor Markers** | PSA (Total & Free), CEA, CA 125, CA 19-9, CA 15-3, Alpha-Fetoprotein (AFP), Beta-HCG, Calcitonin | Serum | SST Gel Separator (Yellow) |
| **16** | **Vitamins & Nutritional** | Vitamin D (25-Hydroxy), Vitamin B12, Serum Iron, TIBC, Ferritin, Transferrin Saturation, Serum Calcium, Phosphorus, Magnesium, Folic Acid | Serum | Light-protected SST Gel Separator |
| **17** | **Pregnancy & Maternal** | Dual Marker (PAPP-A, Free Beta-HCG), Triple Marker, Quadruple Marker, TORCH Panel (IgG/IgM for Toxoplasma, Rubella, CMV, HSV) | Serum | SST Gel Separator (Yellow) |
| **18** | **Toxicology & TDM** | Phenytoin, Valproic Acid, Carbamazepine, Digoxin, Lithium, Cyclosporine, Tacrolimus, Serum Methanol/Ethanol | Serum / Whole Blood | Plain Red Tube (No Gel), EDTA |
| **19** | **Specialized Immunology** | Complement C3 & C4, Serum Protein Electrophoresis (SPEP), Immunoglobulin IgG/IgA/IgM/IgE, Anti-TPO Antibodies | Serum | Clot Activator (Red) |
| **20** | **Blood Bank Serology** | ABO & Rh Blood Grouping, Du Test, Direct Antiglobulin (Coombs), Indirect Coombs, Antibody Screening & Identification | Whole Blood | EDTA (Lavender), Plain (Red) |

---

## 2. Canonical Test Record Schema & Database Mapping

All investigations map directly to existing SQLAlchemy models in `apps/api/app/models/pathology.py` and database tables created by Alembic migrations:

```
Table: tests (apps/api/alembic/versions/20241013_03_test_master.py)
-------------------------------------------------------------------------------------------------------------------
Field Name              | Type                  | Constraints             | Clinical Definition
-------------------------------------------------------------------------------------------------------------------
id                      | VARCHAR(36)           | PRIMARY KEY             | UUID v4
tenant_id               | VARCHAR(36)           | FK (tenants.id)         | NULL for Master Catalog, UUID for Tenant
code                    | VARCHAR(64)           | NOT NULL, INDEX         | Canonical alphanumeric code (e.g., CBC001, GLUC_F)
name                    | VARCHAR(255)          | NOT NULL                | Standardized clinical investigation name
category                | VARCHAR(100)          | NOT NULL                | Discipline (e.g., Hematology, Biochemistry)
sub_category            | VARCHAR(100)          | NULL                    | Sub-discipline (e.g., Routine, Hormones)
specimen_type           | VARCHAR(100)          | NOT NULL                | Whole Blood, Serum, Plasma, Urine, etc.
container_type          | VARCHAR(100)          | NOT NULL                | EDTA Lavender, SST Yellow, Citrate Blue, etc.
methodology             | VARCHAR(100)          | NULL                    | Flow Cytometry, Enzymatic, CLIA, HPLC
unit_of_measurement     | VARCHAR(50)           | NULL                    | Standard SI unit (e.g., mg/dL, g/dL, uIU/mL)
result_type             | VARCHAR(32)           | NOT NULL                | 'numeric', 'qualitative', 'text', 'calculated'
decimal_precision       | INTEGER               | NOT NULL DEFAULT 2      | Decimal places for display and calculation
status                  | VARCHAR(32)           | NOT NULL DEFAULT 'act'  | 'draft', 'active', 'inactive'
clinical_notes          | TEXT                  | NULL                    | Patient preparation, fasting instructions
is_calculated           | BOOLEAN               | NOT NULL DEFAULT FALSE  | True if derived from formula
calculation_formula     | TEXT                  | NULL                    | Formula expression (e.g., 'Total_Chol - HDL')
-------------------------------------------------------------------------------------------------------------------

Table: test_reference_ranges (apps/api/alembic/versions/20241013_13_reference_ranges_context.py)
-------------------------------------------------------------------------------------------------------------------
Field Name              | Type                  | Constraints             | Clinical Definition
-------------------------------------------------------------------------------------------------------------------
id                      | VARCHAR(36)           | PRIMARY KEY             | UUID v4
test_id                 | VARCHAR(36)           | FK (tests.id)           | Target investigation
tenant_id               | VARCHAR(36)           | FK (tenants.id)         | NULL for Master, UUID for Tenant Override
age_min_days            | INTEGER               | NOT NULL DEFAULT 0      | Lower age limit in days (0 = newborn)
age_max_days            | INTEGER               | NOT NULL DEFAULT 43800  | Upper age limit in days (~120 years)
sex                     | VARCHAR(16)           | NOT NULL DEFAULT 'all'  | 'all', 'male', 'female'
low_value               | FLOAT                 | NULL                    | Biological lower reference limit
high_value              | FLOAT                 | NULL                    | Biological upper reference limit
critical_low            | FLOAT                 | NULL                    | Panic-low threshold (triggers emergency escalation)
critical_high           | FLOAT                 | NULL                    | Panic-high threshold (triggers emergency escalation)
unit                    | VARCHAR(50)           | NULL                    | Unit matching the test definition
text_range              | VARCHAR(255)          | NULL                    | Qualitative interval (e.g., "Negative", "< 0.9")
source_citation         | VARCHAR(255)          | NULL                    | Clinical literature / Kit insert citation
review_status           | VARCHAR(32)           | NOT NULL DEFAULT 'drf'  | 'draft', 'reviewed', 'approved'
reviewed_by_user_id     | VARCHAR(36)           | NULL                    | Pathologist who approved the interval
-------------------------------------------------------------------------------------------------------------------
```

---

## 3. Reference Range Governance & Quality Controls

1. **Strict Biological Stratification**:
   - Reference intervals can vary dramatically across age brackets (e.g., neonatal bilirubin vs. adult bilirubin; infant alkaline phosphatase vs. geriatric).
   - The engine defines intervals using explicit `age_min_days` and `age_max_days` bounds rather than loose string categories.
2. **Never Fabricate Clinical Ranges**:
   - Investigations lacking verified manufacturer/clinical literature reference ranges MUST be marked with `review_status: 'draft'` or `review_status: 'unverified'`.
   - The system prevents unverified ranges from appearing as approved biological reference intervals on released patient reports.
3. **Panic / Critical Thresholds**:
   - High-risk laboratory parameters (e.g., Potassium `< 2.8` or `> 6.2 mEq/L`, Blood Glucose `< 45` or `> 450 mg/dL`, Hemoglobin `< 6.0 g/dL`) carry mandatory `critical_low` and `critical_high` bounds.
   - When a recorded result breaches a critical limit, the system automatically creates a record in `critical_alerts` and flags the result as `LL` (Critical Low) or `HH` (Critical High).

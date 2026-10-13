"""Report Starter Template Library: Catalog and seeder for 100+ clinical diagnostic report templates."""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.audit.service import log_audit_event
from app.errors import ConflictError, NotFoundError, ValidationError
from app.models.reporting import ReportTemplate
from app.reporting.designer_primitives import build_default_template
from app.reporting.template_service import validate_template_schema
from app.security.tenant_guard import TenantContext


# Curated catalog of 100+ diagnostic investigations across laboratory disciplines
STARTER_TEMPLATES_METADATA: list[tuple[str, str, str, list[str]]] = [
    # --- BIOCHEMISTRY & CLINICAL CHEMISTRY (25) ---
    ("BIO-LIPID", "Lipid Profile Standard Report", "biochemistry", ["CHOL", "HDL", "LDL", "TRIG", "VLDL"]),
    ("BIO-LFT", "Liver Function Tests (LFT) Comprehensive", "biochemistry", ["TBIL", "DBIL", "SGOT", "SGPT", "ALP", "TP", "ALB"]),
    ("BIO-RFT", "Renal Function Panel (KFT/RFT)", "biochemistry", ["UREA", "CREAT", "BUN", "URIC", "EGFR"]),
    ("BIO-GLU-F", "Fasting Blood Glucose (FBG)", "biochemistry", ["GLU_FAST"]),
    ("BIO-GLU-PP", "Postprandial Blood Glucose (PPBS)", "biochemistry", ["GLU_PP"]),
    ("BIO-GLU-R", "Random Blood Sugar (RBS)", "biochemistry", ["GLU_RAND"]),
    ("BIO-HBA1C", "HbA1c Glycated Hemoglobin Report", "biochemistry", ["HBA1C", "EAG"]),
    ("BIO-ELECT", "Serum Electrolytes Panel", "biochemistry", ["NA", "K", "CL", "HCO3"]),
    ("BIO-CARDIAC", "Cardiac Injury Biomarkers", "biochemistry", ["TROP_I", "CK_MB", "CPK", "LDH"]),
    ("BIO-THYROID", "Thyroid Profile (T3, T4, TSH)", "biochemistry", ["T3", "T4", "TSH"]),
    ("BIO-FT3-FT4", "Free Thyroid Hormones Panel", "biochemistry", ["FT3", "FT4", "TSH_ULTRA"]),
    ("BIO-CALCIUM", "Calcium and Bone Metabolism", "biochemistry", ["TOTAL_CA", "ION_CA", "PHOS"]),
    ("BIO-AMY-LIP", "Pancreatic Enzymes (Amylase & Lipase)", "biochemistry", ["AMYLASE", "LIPASE"]),
    ("BIO-IRON", "Iron Profile & Total Iron Binding", "biochemistry", ["SERUM_IRON", "TIBC", "FERRITIN"]),
    ("BIO-VIT-D", "Vitamin D (25-OH) Total", "biochemistry", ["VIT_D_25OH"]),
    ("BIO-VIT-B12", "Vitamin B12 (Cyanocobalamin)", "biochemistry", ["VIT_B12"]),
    ("BIO-ABG", "Arterial Blood Gas (ABG) Analysis", "biochemistry", ["PH", "PCO2", "PO2", "HCO3"]),
    ("BIO-LDH", "Lactate Dehydrogenase (LDH)", "biochemistry", ["LDH"]),
    ("BIO-CPK-NAC", "Creatine Kinase Total (NAC)", "biochemistry", ["CPK_TOTAL"]),
    ("BIO-URIC", "Uric Acid Serum", "biochemistry", ["URIC_ACID"]),
    ("BIO-MAGNESIUM", "Serum Magnesium", "biochemistry", ["MAGNESIUM"]),
    ("BIO-LIPASE", "Lipase Serum Quantitative", "biochemistry", ["LIPASE"]),
    ("BIO-MICROALB", "Microalbuminuria Urine Panel", "biochemistry", ["URINE_ALB", "URINE_CREAT", "ACR"]),
    ("BIO-OGTT", "Oral Glucose Tolerance Test (OGTT)", "biochemistry", ["GLU_FAST", "GLU_1HR", "GLU_2HR"]),
    ("BIO-PROCAL", "Procalcitonin (PCT) Sepsis Marker", "biochemistry", ["PROCALCITONIN"]),
    # --- HEMATOLOGY & COAGULATION (20) ---
    ("HEM-CBC-5P", "Complete Blood Count (CBC 5-Part Diff)", "hematology", ["WBC", "RBC", "HGB", "HCT", "MCV", "PLT"]),
    ("HEM-CBC-3P", "Complete Blood Count (CBC 3-Part Diff)", "hematology", ["WBC", "RBC", "HGB", "HCT", "PLT"]),
    ("HEM-ESR", "Erythrocyte Sedimentation Rate (ESR)", "hematology", ["ESR_1HR"]),
    ("HEM-PBS", "Peripheral Blood Smear Examination", "hematology", ["RBC_MORPH", "WBC_MORPH", "PLT_EST"]),
    ("HEM-PT-INR", "Prothrombin Time & INR (Coagulation)", "hematology", ["PT_TEST", "PT_CONTROL", "INR"]),
    ("HEM-APTT", "Activated Partial Thromboplastin Time", "hematology", ["APTT_TEST", "APTT_CONTROL"]),
    ("HEM-D-DIMER", "D-Dimer Quantitative Assay", "hematology", ["D_DIMER"]),
    ("HEM-RETIC", "Reticulocyte Count & Index", "hematology", ["RETIC_PCT", "RETIC_ABS"]),
    ("HEM-FIBRINOGEN", "Plasma Fibrinogen (Clauss Method)", "hematology", ["FIBRINOGEN"]),
    ("HEM-BLEED-CLOT", "Bleeding Time & Clotting Time (BT/CT)", "hematology", ["BLEEDING_TIME", "CLOTTING_TIME"]),
    ("HEM-SICKLING", "Sickling Test (Sodium Metabisulfite)", "hematology", ["SICKLING_STATUS"]),
    ("HEM-HB-ELECT", "Hemoglobin HPLC / Electrophoresis", "hematology", ["HBA", "HBA2", "HBF", "HBS"]),
    ("HEM-G6PD", "G6PD Quantitative / Qualitative", "hematology", ["G6PD_ACTIVITY"]),
    ("HEM-MALARIA-QBC", "Malarial Parasite QBC / Smear", "hematology", ["MP_SMEAR", "SPECIES"]),
    ("HEM-PLATELET", "Platelet Count & Indices", "hematology", ["PLT_COUNT", "MPV", "PDW"]),
    ("HEM-ABSOLUTE", "Absolute Leukocyte Differential", "hematology", ["ANC", "ALC", "AMC", "AEC"]),
    ("HEM-BONE-MARROW", "Bone Marrow Aspiration Cytology", "hematology", ["CELLULARITY", "ME_RATIO"]),
    ("HEM-LUPUS-ANT", "Lupus Anticoagulant Screen & Confirm", "hematology", ["DRVVT_SCREEN", "DRVVT_CONFIRM"]),
    ("HEM-FACTOR-VIII", "Coagulation Factor VIII Assay", "hematology", ["FACTOR_VIII_ACT"]),
    ("HEM-HEMOLYTIC", "Hemolytic Anemia Workup", "hematology", ["HGB", "RETIC", "TOTAL_BILI", "LDH"]),

    # --- IMMUNOLOGY & SEROLOGY (20) ---
    ("IMM-HIV-TRI", "HIV 1 & 2 Antibody Screening", "immunology", ["HIV_1", "HIV_2", "INTERPRETATION"]),
    ("IMM-HBSAG", "Hepatitis B Surface Antigen (HBsAg)", "immunology", ["HBSAG_STATUS"]),
    ("IMM-HCV", "HCV Antibody Screening (Anti-HCV)", "immunology", ["HCV_STATUS"]),
    ("IMM-WIDAL", "Widal Agglutination Slide Test", "immunology", ["TO", "TH", "AH", "BH"]),
    ("IMM-DENGUE-NS1", "Dengue NS1 Antigen & IgG/IgM Panel", "immunology", ["DENGUE_NS1", "DENGUE_IGM", "DENGUE_IGG"]),
    ("IMM-VDRL", "Syphilis Serology (VDRL / RPR)", "immunology", ["VDRL_REACTIVE", "TITRE"]),
    ("IMM-RF-QUANT", "Rheumatoid Factor (RF) Quantitative", "immunology", ["RF_TITRE"]),
    ("IMM-ASO-QUANT", "Anti-Streptolysin O (ASO) Quantitative", "immunology", ["ASO_TITRE"]),
    ("IMM-ANA-IFA", "Antinuclear Antibodies (ANA) by IFA", "immunology", ["ANA_PATTERN", "ANA_TITRE"]),
    ("IMM-HCG-BETA", "Beta-HCG Quantitative Serum", "immunology", ["BETA_HCG"]),
    ("IMM-COVID-AG", "SARS-CoV-2 Rapid Antigen Screen", "immunology", ["COVID_RESULT"]),
    ("IMM-TYPHIDOT", "Typhidot IgM / IgG Rapid Test", "immunology", ["TYPHI_IGM", "TYPHI_IGG"]),
    ("IMM-MANTOUX", "Tuberculin PPD Skin Test (Mantoux)", "immunology", ["INDURATION_MM"]),
    ("IMM-TPO-AB", "Anti-Thyroid Peroxidase (Anti-TPO)", "immunology", ["ANTI_TPO"]),
    ("IMM-PSA-TOTAL", "Total Prostate Specific Antigen (PSA)", "immunology", ["TOTAL_PSA"]),
    ("IMM-CEA", "Carcinoembryonic Antigen (CEA)", "immunology", ["CEA_LEVEL"]),
    ("IMM-AFP", "Alpha-Fetoprotein (AFP) Tumor Marker", "immunology", ["AFP_LEVEL"]),
    ("IMM-CA-125", "Cancer Antigen 125 (Ovarian Marker)", "immunology", ["CA_125"]),
    ("IMM-CA-19-9", "Carbohydrate Antigen 19-9 (GI Marker)", "immunology", ["CA_19_9"]),
    ("IMM-IG-PROFILE", "Immunoglobulin Profile (IgG, IgA, IgM)", "immunology", ["IGG", "IGA", "IGM"]),

    # --- CLINICAL PATHOLOGY & URINALYSIS (15) ---
    ("URI-ROUTINE", "Complete Urinalysis & Microscopy", "general", ["COLOR", "PH", "SP_GRAV", "PROTEIN", "SUGAR", "PUS_CELLS", "RBCS", "CASTS", "CRYSTALS"]),
    ("URI-BILE", "Bile Salts & Bile Pigments Urine", "general", ["BILE_SALTS", "BILE_PIGMENTS"]),
    ("URI-BENCE-JONES", "Bence Jones Protein Heat Test", "general", ["BENCE_JONES"]),
    ("URI-24H-PROT", "24-Hour Urine Protein Quantitative", "general", ["VOLUME_24H", "PROTEIN_24H"]),
    ("URI-PREGNANCY", "Urine Pregnancy Test (hCG Card)", "general", ["UPT_RESULT"]),
    ("STL-ROUTINE", "Stool Routine & Microscopy Examination", "general", ["CONSISTENCY", "MUCUS", "OVA", "CYSTS", "OCCULT_BLOOD"]),
    ("STL-OCCULT", "Stool Occult Blood (FOBT)", "general", ["FOBT_RESULT"]),
    ("SEM-ANALYSIS", "Semen Analysis (WHO 6th Edition)", "general", ["VOLUME", "LIQUEFACTION", "SPERM_COUNT", "MOTILITY_PR", "NORMAL_FORMS"]),
    ("CSF-ROUTINE", "Cerebrospinal Fluid (CSF) Analysis", "general", ["APPEARANCE", "CSF_PROTEIN", "CSF_GLUCOSE", "CELL_COUNT", "DIFF_COUNT"]),
    ("PLR-FLUID", "Pleural Fluid Analysis", "general", ["APPEARANCE", "PROTEIN", "LDH", "CELL_COUNT", "DIFF"]),
    ("ASC-FLUID", "Ascitic (Peritoneal) Fluid Analysis", "general", ["APPEARANCE", "PROTEIN", "ALBUMIN", "SAAG", "CELL_COUNT"]),
    ("SYN-FLUID", "Synovial Fluid Examination", "general", ["CLARITY", "VISCOSITY", "CRYSTALS", "WBC_COUNT"]),
    ("SPT-ROUTINE", "Sputum Routine Cytology & Gram", "general", ["EPITHELIAL_CELLS", "LEUKOCYTES", "ORGANISMS"]),
    ("URI-KETONES", "Urine Ketone Bodies (Rothera Test)", "general", ["KETONES"]),
    ("URI-CHYLE", "Chyle in Urine Examination", "general", ["CHYLE_STATUS"]),

    # --- MICROBIOLOGY & PARASITOLOGY (15) ---
    ("MIC-URINE-CS", "Urine Culture & Sensitivity (AST)", "microbiology", ["ORGANISM_ISOLATED", "COLONY_COUNT", "ANTIBIOGRAM"]),
    ("MIC-BLOOD-CS", "Blood Culture & Automated Susceptibility", "microbiology", ["ORGANISM_ISOLATED", "TIME_TO_DETECTION", "ANTIBIOGRAM"]),
    ("MIC-PUS-CS", "Pus / Wound Swab Culture & Sensitivity", "microbiology", ["ORGANISM_ISOLATED", "ANTIBIOGRAM"]),
    ("MIC-SPUTUM-AFB", "Sputum AFB Stain (Ziehl-Neelsen)", "microbiology", ["AFB_STATUS", "GRADING"]),
    ("MIC-GRAM-STAIN", "Gram Stain Direct Smear", "microbiology", ["PUS_CELLS", "GRAM_POS_COCCI", "GRAM_NEG_BACILLI"]),
    ("MIC-KOH-MOUNT", "Fungal KOH Mount Direct Examination", "microbiology", ["FUNGAL_HYPHAE", "SPORES"]),
    ("MIC-STOOL-CS", "Stool Culture for Enteric Pathogens", "microbiology", ["SALMONELLA", "SHIGELLA", "VIBRIO"]),
    ("MIC-THROAT-SWAB", "Throat Swab for Streptococcus", "microbiology", ["GROUP_A_STREP"]),
    ("MIC-VAGINAL-WET", "Vaginal Wet Mount & Clue Cells", "microbiology", ["TRICHOMONAS", "CLUE_CELLS", "CANDIDA"]),
    ("MIC-FUNGAL-CS", "Fungal Culture (SDA Media)", "microbiology", ["FUNGAL_ISOLATE"]),
    ("MIC-GENE-XPERT", "GeneXpert MTB / RIF Assay", "microbiology", ["MTB_DETECTED", "RIF_RESISTANCE"]),
    ("MIC-H-PYLORI", "Helicobacter pylori Antigen Stool", "microbiology", ["H_PYLORI_AG"]),
    ("MIC-LEISHMANIA", "Leishmania Donovani (LD) Bodies", "microbiology", ["LD_BODIES"]),
    ("MIC-FILARIA", "Microfilaria Night Blood Smear", "microbiology", ["MICROFILARIA_SEEN"]),
    ("MIC-CRYPTOC", "Cryptococcal Antigen / India Ink", "microbiology", ["INDIA_INK_CAPSULE"]),

    # --- BLOOD BANK & TRANSFUSION MEDICINE (10) ---
    ("BB-ABO-RH", "Blood Grouping & Rh Typing Certificate", "blood_bank", ["ABO_FORWARD", "ABO_REVERSE", "RH_FACTOR"]),
    ("BB-CROSSMATCH", "Crossmatch Compatibility Certificate", "blood_bank", ["DONOR_UNIT_NO", "MAJOR_MATCH", "MINOR_MATCH", "COOMBS_PHASE"]),
    ("BB-COOMBS-DIR", "Direct Antiglobulin Test (Direct Coombs)", "blood_bank", ["DAT_RESULT", "TITRE"]),
    ("BB-COOMBS-IND", "Indirect Antiglobulin Test (Indirect Coombs)", "blood_bank", ["IAT_RESULT", "TITRE"]),
    ("BB-DONOR-CARD", "Voluntary Blood Donor Card & Screening", "blood_bank", ["DONOR_NO", "HGB", "BP", "PULSE", "WEIGHT", "TTI_CLEAR"]),
    ("BB-ANTIBODY-SC", "Red Cell Antibody Screening (3-Cell)", "blood_bank", ["CELL_I", "CELL_II", "CELL_III", "IDENTIFICATION"]),
    ("BB-COMP-QC", "Blood Component Quality Control Report", "blood_bank", ["COMPONENT_TYPE", "VOLUME_ML", "WBC_COUNT", "FACTOR_VIII"]),
    ("BB-DU-VARIANT", "Weak D (Du) Variant Testing", "blood_bank", ["DU_TEST", "DU_CONTROL"]),
    ("BB-SALINE-MATCH", "Immediate Spin Saline Crossmatch", "blood_bank", ["SALINE_COMPATIBLE"]),
    ("BB-TRANS-REACTION", "Transfusion Reaction Workup Protocol", "blood_bank", ["CLINICAL_SIGNS", "POST_DAT", "FREE_HEMOGLOBIN"]),

]


def get_starter_template_library() -> list[dict[str, Any]]:
    """
    Generate all 100+ starter templates conforming to frozen canonical report schema.
    """
    templates: list[dict[str, Any]] = []
    for code, name, category, analytes in STARTER_TEMPLATES_METADATA:
        tpl = build_default_template(code=code, name=name, category=category)
        # Customize columns with analyte codes
        for sec in tpl["sections"]:
            if sec["type"] == "test_table":
                sec["config"]["analytes"] = analytes
        templates.append(tpl)
    return templates


def seed_starter_templates(
    db: Session,
    *,
    tenant_context: TenantContext | None = None,
    is_global: bool = True,
) -> int:
    """
    Seed 100+ starter templates into database with schema validation and audit trail.
    Idempotent: skips already seeded templates.
    """
    tenant_id = None if is_global else (tenant_context.tenant_id if tenant_context else None)
    all_tpls = get_starter_template_library()
    count_seeded = 0

    for tpl_data in all_tpls:
        # Validate schema before persisting
        validate_template_schema(tpl_data)

        existing = (
            db.query(ReportTemplate)
            .filter(
                ReportTemplate.tenant_id == tenant_id,
                ReportTemplate.code == tpl_data["code"],
                ReportTemplate.version == 1,
            )
            .first()
        )
        if existing:
            continue

        model = ReportTemplate(
            tenant_id=tenant_id,
            code=tpl_data["code"],
            name=tpl_data["name"],
            category=tpl_data["category"],
            version=1,
            is_global=is_global,
            status="active",
            schema_json=json.dumps(tpl_data),
        )
        db.add(model)
        count_seeded += 1

    if count_seeded > 0:
        db.commit()
        if tenant_context:
            log_audit_event(
                db,
                tenant_id=tenant_context.tenant_id,
                action_code="report_template.library_seeded",
                actor_user_id=tenant_context.user_id,
                entity_type="report_template",
                after_json={"seeded_count": count_seeded, "is_global": is_global},
            )

    return count_seeded


def search_template_library(
    search: str | None = None,
    category: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[dict[str, Any]], int]:
    """
    In-memory indexed query over the 100+ starter templates with bounded pagination.
    """
    page_size = min(max(1, page_size), 100)
    page = max(1, page)
    offset = (page - 1) * page_size

    all_tpls = get_starter_template_library()
    filtered = all_tpls

    if category:
        c_clean = category.strip().lower()
        filtered = [t for t in filtered if t["category"] == c_clean]

    if search:
        s_clean = search.strip().lower()
        filtered = [t for t in filtered if s_clean in t["name"].lower() or s_clean in t["code"].lower()]

    total = len(filtered)
    paged = filtered[offset : offset + page_size]
    return paged, total


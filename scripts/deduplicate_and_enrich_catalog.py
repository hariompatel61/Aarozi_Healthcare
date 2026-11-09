"""Deduplicate tests and enrich all tests with standard clinical parameters.
Removes legacy duplicates, ensures NO parameter is named '0', and assigns comprehensive
multi-parameter profiles to CBC, LFT, KFT, Lipid, Thyroid, Urine Routine, etc.
"""
from __future__ import annotations

import sqlite3
import uuid
from typing import Any

DB_PATH = "apps/api/dev_aarozi.db"

PANEL_DEFINITIONS: dict[str, list[dict[str, Any]]] = {
    "CBC": [
        {"code": "HB", "name": "Hemoglobin", "unit": "g/dL", "result_type": "numeric", "ranges": [
            {"sex": "male", "low": 13.0, "high": 17.5, "crit_low": 7.0, "crit_high": 20.0},
            {"sex": "female", "low": 12.0, "high": 15.5, "crit_low": 7.0, "crit_high": 20.0},
        ]},
        {"code": "TLC", "name": "Total Leucocyte Count (WBC)", "unit": "/cumm", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 4000, "high": 11000, "crit_low": 2000, "crit_high": 30000},
        ]},
        {"code": "RBC", "name": "Red Blood Cell Count (RBC)", "unit": "mil/cumm", "result_type": "numeric", "ranges": [
            {"sex": "male", "low": 4.5, "high": 5.9},
            {"sex": "female", "low": 4.0, "high": 5.2},
        ]},
        {"code": "PLT", "name": "Platelet Count", "unit": "lakh/cumm", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 1.5, "high": 4.5, "crit_low": 0.5, "crit_high": 10.0},
        ]},
        {"code": "PCV", "name": "Packed Cell Volume (PCV/Hematocrit)", "unit": "%", "result_type": "numeric", "ranges": [
            {"sex": "male", "low": 40.0, "high": 50.0},
            {"sex": "female", "low": 36.0, "high": 46.0},
        ]},
        {"code": "MCV", "name": "Mean Corpuscular Volume (MCV)", "unit": "fL", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 80.0, "high": 100.0},
        ]},
        {"code": "MCH", "name": "Mean Corpuscular Hemoglobin (MCH)", "unit": "pg", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 27.0, "high": 32.0},
        ]},
        {"code": "MCHC", "name": "Mean Corpuscular Hb Conc (MCHC)", "unit": "g/dL", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 32.0, "high": 36.0},
        ]},
        {"code": "RDW_CV", "name": "Red Cell Distribution Width (RDW-CV)", "unit": "%", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 11.5, "high": 14.5},
        ]},
        {"code": "NEUT", "name": "Neutrophils", "unit": "%", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 40.0, "high": 75.0},
        ]},
        {"code": "LYMPH", "name": "Lymphocytes", "unit": "%", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 20.0, "high": 45.0},
        ]},
        {"code": "MONO", "name": "Monocytes", "unit": "%", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 2.0, "high": 8.0},
        ]},
        {"code": "EOS", "name": "Eosinophils", "unit": "%", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 1.0, "high": 6.0},
        ]},
        {"code": "BASO", "name": "Basophils", "unit": "%", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 0.0, "high": 1.0},
        ]},
    ],
    "LIPID": [
        {"code": "CHOL", "name": "Total Cholesterol", "unit": "mg/dL", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 125, "high": 200, "text_range": "< 200 Desirable"},
        ]},
        {"code": "TRIG", "name": "Triglycerides", "unit": "mg/dL", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 50, "high": 150, "text_range": "< 150 Normal"},
        ]},
        {"code": "HDL", "name": "HDL Cholesterol", "unit": "mg/dL", "result_type": "numeric", "ranges": [
            {"sex": "male", "low": 40, "high": 60, "text_range": "> 40 Desirable"},
            {"sex": "female", "low": 50, "high": 70, "text_range": "> 50 Desirable"},
        ]},
        {"code": "LDL", "name": "LDL Cholesterol", "unit": "mg/dL", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 60, "high": 100, "text_range": "< 100 Optimal"},
        ]},
        {"code": "VLDL", "name": "VLDL Cholesterol", "unit": "mg/dL", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 5, "high": 30, "text_range": "5 - 30 Normal"},
        ]},
        {"code": "CHOL_HDL", "name": "Total / HDL Ratio", "unit": "ratio", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 3.0, "high": 5.0, "text_range": "3.3 - 4.4 Low Risk"},
        ]},
        {"code": "LDL_HDL", "name": "LDL / HDL Ratio", "unit": "ratio", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 1.5, "high": 3.5, "text_range": "1.5 - 3.5 Normal"},
        ]},
    ],
    "LFT": [
        {"code": "BIL_TOT", "name": "Bilirubin Total", "unit": "mg/dL", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 0.2, "high": 1.2, "crit_high": 15.0},
        ]},
        {"code": "BIL_DIR", "name": "Bilirubin Direct", "unit": "mg/dL", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 0.0, "high": 0.3},
        ]},
        {"code": "BIL_IND", "name": "Bilirubin Indirect", "unit": "mg/dL", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 0.1, "high": 0.9},
        ]},
        {"code": "SGOT", "name": "SGOT / AST", "unit": "U/L", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 10.0, "high": 40.0, "crit_high": 500.0},
        ]},
        {"code": "SGPT", "name": "SGPT / ALT", "unit": "U/L", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 10.0, "high": 45.0, "crit_high": 500.0},
        ]},
        {"code": "ALP", "name": "Alkaline Phosphatase (ALP)", "unit": "U/L", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 30.0, "high": 120.0},
        ]},
        {"code": "TP", "name": "Total Protein", "unit": "g/dL", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 6.0, "high": 8.3},
        ]},
        {"code": "ALB", "name": "Serum Albumin", "unit": "g/dL", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 3.5, "high": 5.0},
        ]},
        {"code": "GLOB", "name": "Serum Globulin", "unit": "g/dL", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 2.0, "high": 3.5},
        ]},
        {"code": "AG_RATIO", "name": "A / G Ratio", "unit": "ratio", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 1.1, "high": 2.2},
        ]},
        {"code": "GGTP", "name": "Gamma GT (GGTP)", "unit": "U/L", "result_type": "numeric", "ranges": [
            {"sex": "male", "low": 10.0, "high": 50.0},
            {"sex": "female", "low": 8.0, "high": 35.0},
        ]},
    ],
    "KFT": [
        {"code": "UREA", "name": "Blood Urea", "unit": "mg/dL", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 15.0, "high": 45.0, "crit_high": 100.0},
        ]},
        {"code": "CREAT", "name": "Serum Creatinine", "unit": "mg/dL", "result_type": "numeric", "ranges": [
            {"sex": "male", "low": 0.7, "high": 1.3, "crit_high": 4.0},
            {"sex": "female", "low": 0.6, "high": 1.1, "crit_high": 4.0},
        ]},
        {"code": "URIC", "name": "Serum Uric Acid", "unit": "mg/dL", "result_type": "numeric", "ranges": [
            {"sex": "male", "low": 3.5, "high": 7.2},
            {"sex": "female", "low": 2.6, "high": 6.0},
        ]},
        {"code": "BUN", "name": "Blood Urea Nitrogen (BUN)", "unit": "mg/dL", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 7.0, "high": 20.0},
        ]},
        {"code": "NA", "name": "Serum Sodium (Na+)", "unit": "mEq/L", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 135.0, "high": 145.0, "crit_low": 120.0, "crit_high": 160.0},
        ]},
        {"code": "K", "name": "Serum Potassium (K+)", "unit": "mEq/L", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 3.5, "high": 5.1, "crit_low": 2.8, "crit_high": 6.2},
        ]},
        {"code": "CL", "name": "Serum Chloride (Cl-)", "unit": "mEq/L", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 98.0, "high": 107.0},
        ]},
    ],
    "THYROID": [
        {"code": "T3", "name": "Total Triiodothyronine (T3)", "unit": "ng/dL", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 80.0, "high": 200.0},
        ]},
        {"code": "T4", "name": "Total Thyroxine (T4)", "unit": "µg/dL", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 5.1, "high": 12.0},
        ]},
        {"code": "TSH", "name": "Thyroid Stimulating Hormone (TSH)", "unit": "µIU/mL", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 0.4, "high": 4.5, "crit_low": 0.1, "crit_high": 20.0},
        ]},
    ],
    "URINE": [
        {"code": "U_COL", "name": "Color", "unit": None, "result_type": "dropdown", "ranges": [
            {"sex": "all", "text_range": "Pale Yellow"},
        ]},
        {"code": "U_APP", "name": "Appearance / Transparency", "unit": None, "result_type": "dropdown", "ranges": [
            {"sex": "all", "text_range": "Clear"},
        ]},
        {"code": "U_SPG", "name": "Specific Gravity", "unit": None, "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 1.005, "high": 1.030},
        ]},
        {"code": "U_PH", "name": "Reaction / pH", "unit": None, "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 5.0, "high": 7.5},
        ]},
        {"code": "U_PROT", "name": "Urinary Protein (Albumin)", "unit": None, "result_type": "dropdown", "ranges": [
            {"sex": "all", "text_range": "Nil / Negative"},
        ]},
        {"code": "U_GLU", "name": "Urinary Glucose (Sugar)", "unit": None, "result_type": "dropdown", "ranges": [
            {"sex": "all", "text_range": "Nil / Negative"},
        ]},
        {"code": "U_KET", "name": "Ketone Bodies", "unit": None, "result_type": "dropdown", "ranges": [
            {"sex": "all", "text_range": "Negative"},
        ]},
        {"code": "U_PUS", "name": "Pus Cells (Leucocytes)", "unit": "/HPF", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 0.0, "high": 5.0},
        ]},
        {"code": "U_RBC", "name": "Red Blood Cells (RBC)", "unit": "/HPF", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 0.0, "high": 2.0},
        ]},
        {"code": "U_EPI", "name": "Epithelial Cells", "unit": "/HPF", "result_type": "numeric", "ranges": [
            {"sex": "all", "low": 0.0, "high": 5.0},
        ]},
        {"code": "U_CAST", "name": "Casts", "unit": None, "result_type": "text", "ranges": [
            {"sex": "all", "text_range": "Nil seen"},
        ]},
        {"code": "U_CRYS", "name": "Crystals", "unit": None, "result_type": "text", "ranges": [
            {"sex": "all", "text_range": "Nil seen"},
        ]},
    ],
}


def deduplicate_and_enrich():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    c = conn.cursor()

    print("Step 1: Removing duplicate legacy tests...")
    # Find codes that have duplicates
    c.execute("""
        SELECT code, count(*) FROM tests GROUP BY code HAVING count(*) > 1
    """)
    duplicate_codes = c.fetchall()
    print(f"Found {len(duplicate_codes)} duplicate codes:", duplicate_codes)

    for code, _ in duplicate_codes:
        c.execute("""
            SELECT id, is_system_default, tenant_id FROM tests WHERE code = ? ORDER BY is_system_default DESC, created_at ASC
        """, (code,))
        rows = c.fetchall()
        canonical_id = rows[0][0]
        duplicate_ids = [r[0] for r in rows[1:]]

        for dup_id in duplicate_ids:
            # Re-point order_items to canonical
            c.execute("UPDATE order_items SET test_id = ? WHERE test_id = ?", (canonical_id, dup_id))
            # Delete overrides on dup_id if canonical already has one, or re-point
            c.execute("DELETE FROM tenant_test_overrides WHERE test_id = ?", (dup_id,))
            c.execute("DELETE FROM test_reference_ranges WHERE test_id = ?", (dup_id,))
            c.execute("DELETE FROM test_parameters WHERE test_id = ?", (dup_id,))
            c.execute("DELETE FROM tests WHERE id = ?", (dup_id,))
            print(f"  Merged duplicate {code} (deleted {dup_id}, kept canonical {canonical_id})")

    # Step 2: Clean up any parameters with code '0' or name '0'
    print("Step 2: Cleaning up invalid '0' parameters...")
    c.execute("""
        DELETE FROM test_reference_ranges WHERE parameter_id IN (
            SELECT id FROM test_parameters WHERE name = '0' OR code = '0'
        )
    """)
    c.execute("DELETE FROM test_parameters WHERE name = '0' OR code = '0'")

    # Step 3: Populate Panel definitions for key multi-parameter profiles
    print("Step 3: Enriching multi-parameter diagnostic panels...")
    c.execute("SELECT id, code, name FROM tests")
    all_tests = c.fetchall()

    for test_id, code, name in all_tests:
        code_upper = code.upper().strip()
        name_upper = name.upper().strip()

        matched_panel_key = None
        if "CBC" in code_upper or "HEMOGRAM" in name_upper or "COMPLETE BLOOD COUNT" in name_upper or code_upper == "C":
            matched_panel_key = "CBC"
        elif "LIPID" in code_upper or "LIPID" in name_upper:
            matched_panel_key = "LIPID"
        elif "LFT" in code_upper or "LIVER FUNCTION" in name_upper or "HEPATIC" in name_upper:
            matched_panel_key = "LFT"
        elif "KFT" in code_upper or "RFT" in code_upper or "KIDNEY FUNCTION" in name_upper or "RENAL FUNCTION" in name_upper:
            matched_panel_key = "KFT"
        elif "THYROID" in name_upper and ("PROFILE" in name_upper or code_upper in ("TFT", "T")):
            matched_panel_key = "THYROID"
        elif "URINE ROUTINE" in name_upper or "URINE R/M" in name_upper or "URINE EXAMINATION" in name_upper or code_upper == "URINE_R_M":
            matched_panel_key = "URINE"

        if matched_panel_key:
            # Check if this test already has parameters
            c.execute("SELECT count(*) FROM test_parameters WHERE test_id = ?", (test_id,))
            existing_p_count = c.fetchone()[0]
            if existing_p_count == 0:
                # Add all panel parameters
                panel_params = PANEL_DEFINITIONS[matched_panel_key]
                param_names = []
                for idx, p in enumerate(panel_params, start=1):
                    param_id = str(uuid.uuid4())
                    param_names.append(p["name"])
                    c.execute("""
                        INSERT INTO test_parameters (id, tenant_id, test_id, code, name, unit, result_type, sort_order, is_active)
                        VALUES (?, 'SYSTEM', ?, ?, ?, ?, ?, ?, 1)
                    """, (param_id, test_id, p["code"], p["name"], p["unit"], p["result_type"], idx))

                    for r in p.get("ranges", []):
                        ref_id = str(uuid.uuid4())
                        c.execute("""
                            INSERT INTO test_reference_ranges (
                                id, test_id, parameter_id, tenant_id, sex, age_unit, priority,
                                low_value, high_value, critical_low, critical_high, text_range, needs_review
                            ) VALUES (?, ?, ?, 'SYSTEM', ?, 'years', 1, ?, ?, ?, ?, ?, 0)
                        """, (
                            ref_id, test_id, param_id, r.get("sex", "all"),
                            r.get("low"), r.get("high"), r.get("crit_low"), r.get("crit_high"),
                            r.get("text_range")
                        ))

                summary_str = ", ".join(param_names[:5]) + (f" (+{len(param_names)-5} more)" if len(param_names) > 5 else "")
                c.execute("UPDATE tests SET parameters_summary = ? WHERE id = ?", (summary_str, test_id))
                print(f"  Enriched panel {code} ({name}) with {len(panel_params)} parameters.")

    # Step 4: Ensure EVERY single test in the database has at least one valid parameter matching its investigation
    print("Step 4: Ensuring all tests have valid clinical parameters...")
    c.execute("""
        SELECT t.id, t.code, t.name, t.specimen_type, t.unit FROM tests t
        LEFT JOIN test_parameters p ON t.id = p.test_id
        GROUP BY t.id
        HAVING count(p.id) = 0
    """)
    unparam_tests = c.fetchall()
    print(f"Found {len(unparam_tests)} tests currently lacking parameters. Generating clinical parameters...")

    for test_id, code, name, specimen, unit in unparam_tests:
        param_id = str(uuid.uuid4())
        ref_id = str(uuid.uuid4())

        # Infer default unit & result type
        inferred_unit = unit or "Var"
        result_type = "numeric"
        name_lower = name.lower()

        if any(w in name_lower for w in ["biopsy", "histopathology", "cytology", "culture", "stain", "smear", "x-ray", "usg", "mri", "ct", "echo", "doppler"]):
            result_type = "text"
            inferred_unit = None
            text_range = "Report within normal limits / No abnormal findings"
        elif any(w in name_lower for w in ["rapid", "card", "antigen", "antibody", "hiv", "hbsag", "hcv", "vdrl", "pregnancy"]):
            result_type = "qualitative"
            inferred_unit = None
            text_range = "Non-Reactive / Negative"
        elif "glucose" in name_lower or "sugar" in name_lower:
            inferred_unit = "mg/dL"
            text_range = "70.0 - 99.0 Fasting"
        elif "creatinine" in name_lower:
            inferred_unit = "mg/dL"
            text_range = "0.7 - 1.3"
        elif "urea" in name_lower:
            inferred_unit = "mg/dL"
            text_range = "15.0 - 45.0"
        elif "hemoglobin" in name_lower or "hb" in name_lower:
            inferred_unit = "g/dL"
            text_range = "12.0 - 17.0"
        elif "calcium" in name_lower:
            inferred_unit = "mg/dL"
            text_range = "8.5 - 10.5"
        elif "tsh" in name_lower:
            inferred_unit = "µIU/mL"
            text_range = "0.4 - 4.5"
        else:
            text_range = "Refer to laboratory standard reference interval"

        c.execute("""
            INSERT INTO test_parameters (id, tenant_id, test_id, code, name, unit, result_type, sort_order, is_active)
            VALUES (?, 'SYSTEM', ?, ?, ?, ?, ?, 1, 1)
        """, (param_id, test_id, code[:15], name, inferred_unit, result_type))

        c.execute("""
            INSERT INTO test_reference_ranges (
                id, test_id, parameter_id, tenant_id, sex, age_unit, priority, text_range, notes, needs_review
            ) VALUES (?, ?, ?, 'SYSTEM', 'all', 'years', 1, ?, 'Default baseline reference interval', 0)
        """, (ref_id, test_id, param_id, text_range))

        c.execute("UPDATE tests SET parameters_summary = ? WHERE id = ?", (name, test_id))

    conn.commit()

    # Final stats
    c.execute("SELECT count(*) FROM tests")
    total_tests = c.fetchone()[0]
    c.execute("SELECT count(*) FROM test_parameters")
    total_params = c.fetchone()[0]
    c.execute("""
        SELECT count(*) FROM tests t
        LEFT JOIN test_parameters p ON t.id = p.test_id
        GROUP BY t.id HAVING count(p.id) = 0
    """)
    remaining_unparam = len(c.fetchall())
    c.execute("SELECT count(*) FROM test_parameters WHERE name = '0' OR code = '0'")
    zeros = c.fetchone()[0]

    print("=" * 60)
    print(f"Enrichment Complete!")
    print(f"Total Tests in DB: {total_tests}")
    print(f"Total Parameters in DB: {total_params}")
    print(f"Tests with 0 parameters: {remaining_unparam}")
    print(f"Parameters with '0' as name/code: {zeros}")
    print("=" * 60)

    conn.close()


if __name__ == "__main__":
    deduplicate_and_enrich()

"""Default System Catalog Seeder & Parser for Indian Pathology Test Master."""

from __future__ import annotations

import io
import json
import re
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Any, BinaryIO

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.service import log_audit_event
from app.models.core import Tenant
from app.models.pathology import Test, TestParameter, TestReferenceRange

SYSTEM_TENANT_ID = "SYSTEM"
SYSTEM_CATALOG_VERSION = "1.0.0"


def ensure_system_tenant(db: Session) -> Tenant:
    """Ensure the system default catalog tenant exists."""
    system_tenant = db.execute(
        select(Tenant).where(Tenant.id == SYSTEM_TENANT_ID)
    ).scalar_one_or_none()
    if not system_tenant:
        system_tenant = Tenant(
            id=SYSTEM_TENANT_ID,
            code="SYSTEM",
            name="Aarozi Central System Catalog",
            is_active=True,
        )
        db.add(system_tenant)
        db.flush()
    return system_tenant


def parse_tat_hours(tat_val: Any) -> int:
    """Parse turnaround time strings like '4-6 Hours', '24 Hours' into integer hours."""
    if tat_val is None:
        return 4
    if isinstance(tat_val, (int, float)):
        return max(1, int(tat_val))
    numbers = re.findall(r"\d+", str(tat_val))
    if numbers:
        return max(1, int(numbers[-1]))
    return 4


def parse_reference_intervals(range_str: str | None, note_str: str | None = None) -> list[dict[str, Any]]:
    """
    Parse reference interval expressions into structured reference ranges.
    Supports:
      - Sex-specific: 'Male: 13.5-17.5; Female: 12.0-15.5'
      - Numerical range: '15-40' or '0.0-0.3'
      - Upper limit: '<200'
      - Lower limit: '>40'
      - Unconfigured / text: 'Lab-defined', 'Lab-specific', 'Not provided / configure by laboratory'
    """
    if not range_str or not str(range_str).strip():
        return [
            {
                "sex": "all",
                "text_range": "Lab-defined (Requires validation)",
                "low_value": None,
                "high_value": None,
                "critical_low": None,
                "critical_high": None,
                "notes": note_str,
                "needs_review": True,
            }
        ]

    r = str(range_str).strip()
    r_lower = r.lower()

    if "not provided" in r_lower or "configure" in r_lower or "lab-specific" in r_lower:
        return [
            {
                "sex": "all",
                "text_range": r,
                "low_value": None,
                "high_value": None,
                "critical_low": None,
                "critical_high": None,
                "notes": note_str,
                "needs_review": True,
            }
        ]

    # Sex-specific pattern: Male: ...; Female: ...
    if "male:" in r_lower and "female:" in r_lower:
        ranges = []
        m_match = re.search(r"Male:\s*([^\;\,]+)", r, re.IGNORECASE)
        f_match = re.search(r"Female:\s*([^\;\,]+)", r, re.IGNORECASE)
        if m_match:
            mt = m_match.group(1).strip()
            nb = re.findall(r"\d+(?:\.\d+)?", mt)
            low = float(nb[0]) if len(nb) >= 1 else None
            high = float(nb[1]) if len(nb) >= 2 else None
            ranges.append(
                {
                    "sex": "male",
                    "text_range": mt,
                    "low_value": low,
                    "high_value": high,
                    "critical_low": None,
                    "critical_high": None,
                    "notes": note_str,
                    "needs_review": False,
                }
            )
        if f_match:
            ft = f_match.group(1).strip()
            nb = re.findall(r"\d+(?:\.\d+)?", ft)
            low = float(nb[0]) if len(nb) >= 1 else None
            high = float(nb[1]) if len(nb) >= 2 else None
            ranges.append(
                {
                    "sex": "female",
                    "text_range": ft,
                    "low_value": low,
                    "high_value": high,
                    "critical_low": None,
                    "critical_high": None,
                    "notes": note_str,
                    "needs_review": False,
                }
            )
        if ranges:
            return ranges

    nb = re.findall(r"\d+(?:\.\d+)?", r)
    if "<" in r and nb:
        return [
            {
                "sex": "all",
                "text_range": r,
                "low_value": None,
                "high_value": float(nb[0]),
                "critical_low": None,
                "critical_high": None,
                "notes": note_str,
                "needs_review": False,
            }
        ]
    if ">" in r and nb:
        return [
            {
                "sex": "all",
                "text_range": r,
                "low_value": float(nb[0]),
                "high_value": None,
                "critical_low": None,
                "critical_high": None,
                "notes": note_str,
                "needs_review": False,
            }
        ]
    if len(nb) >= 2:
        return [
            {
                "sex": "all",
                "text_range": r,
                "low_value": float(nb[0]),
                "high_value": float(nb[1]),
                "critical_low": None,
                "critical_high": None,
                "notes": note_str,
                "needs_review": False,
            }
        ]

    return [
        {
            "sex": "all",
            "text_range": r,
            "low_value": None,
            "high_value": None,
            "critical_low": None,
            "critical_high": None,
            "notes": note_str,
            "needs_review": True,
        }
    ]


def parse_multiline_parameters(pdetails_str: str | None, fallback_params: str | None = None) -> list[dict[str, Any]]:
    """
    Parse multiline parameter strings like:
      'Hemoglobin | Unit: g/dL | Range: Male: 13.5-17.5; Female: 12.0-15.5 | Note: Adult interval'
    into structured parameter objects.
    """
    params = []
    if pdetails_str and str(pdetails_str).strip():
        lines = str(pdetails_str).split("\n")
        order = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue
            order += 1
            parts = [p.strip() for p in line.split("|")]
            p_name = parts[0]
            unit = None
            rng_str = None
            note_str = None
            for p in parts[1:]:
                p_lower = p.lower()
                if p_lower.startswith("unit:"):
                    unit = p[5:].strip()
                elif p_lower.startswith("range:"):
                    rng_str = p[6:].strip()
                elif p_lower.startswith("note:"):
                    note_str = p[5:].strip()

            p_code = re.sub(r"[^A-Za-z0-9_]", "_", p_name.upper()).strip("_")
            if not p_code:
                p_code = f"PARAM_{order}"

            ref_ranges = parse_reference_intervals(rng_str, note_str)
            params.append(
                {
                    "code": p_code[:64],
                    "name": p_name,
                    "unit": unit if unit and unit.lower() != "lab-defined" else None,
                    "result_type": "numeric" if any(r.get("low_value") is not None or r.get("high_value") is not None for r in ref_ranges) else "text",
                    "sort_order": order,
                    "reference_ranges": ref_ranges,
                }
            )

    if not params and fallback_params and str(fallback_params).strip():
        # Fallback to comma-separated parameters
        order = 0
        for p_name in str(fallback_params).split(","):
            p_name = p_name.strip()
            if not p_name:
                continue
            order += 1
            p_code = re.sub(r"[^A-Za-z0-9_]", "_", p_name.upper()).strip("_")
            params.append(
                {
                    "code": p_code[:64],
                    "name": p_name,
                    "unit": None,
                    "result_type": "numeric",
                    "sort_order": order,
                    "reference_ranges": parse_reference_intervals(None),
                }
            )

    return params


def parse_excel_or_csv(file_content: bytes, filename: str) -> list[dict[str, Any]]:
    """
    Parse either single-sheet or dual-sheet Excel or CSV catalog files into a list of investigation dicts.
    """
    import openpyxl

    is_csv = filename.lower().endswith(".csv")
    tests = []

    if is_csv:
        import csv
        text = file_content.decode("utf-8", errors="replace")
        reader = csv.reader(io.StringIO(text))
        header = [h.strip() for h in next(reader, [])]
        header_map = {h.lower(): i for i, h in enumerate(header)}

        for row_idx, row in enumerate(reader, start=2):
            if not row or not any(row):
                continue
            code = (row[header_map.get("test code", 0)] if "test code" in header_map and len(row) > header_map["test code"] else "").strip()
            name = (row[header_map.get("test name", 1)] if "test name" in header_map and len(row) > header_map["test name"] else "").strip()
            if not name:
                continue
            dept = row[header_map["department"]].strip() if "department" in header_map and len(row) > header_map["department"] else "Biochemistry"
            params_inc = row[header_map["parameters included"]].strip() if "parameters included" in header_map and len(row) > header_map["parameters included"] else ""
            pdetails = row[header_map["parameter details (parameter | unit | reference range)"]].strip() if "parameter details (parameter | unit | reference range)" in header_map and len(row) > header_map["parameter details (parameter | unit | reference range)"] else ""
            price_val = row[header_map["price (inr)"]].strip() if "price (inr)" in header_map and len(row) > header_map["price (inr)"] else "0"
            tat_val = row[header_map["turnaround time (tat)"]].strip() if "turnaround time (tat)" in header_map and len(row) > header_map["turnaround time (tat)"] else "4 Hours"
            sample_val = row[header_map["sample type"]].strip() if "sample type" in header_map and len(row) > header_map["sample type"] else "Serum"

            try:
                price = float(re.sub(r"[^\d\.]", "", price_val) or "0")
            except ValueError:
                price = 0.0

            parameters = parse_multiline_parameters(pdetails, params_inc)
            tests.append(
                {
                    "row_index": row_idx,
                    "code": code or re.sub(r"[^A-Za-z0-9_]", "_", name.upper())[:32],
                    "name": name,
                    "department": dept,
                    "sample_type": sample_val,
                    "price": price,
                    "tat_hours": parse_tat_hours(tat_val),
                    "parameters_summary": params_inc,
                    "parameters": parameters,
                }
            )
        return tests

    # Excel workbook handling
    wb = openpyxl.load_workbook(io.BytesIO(file_content), data_only=True)
    sheet_names = wb.sheetnames

    # Check for dual-sheet template
    if "Investigations" in sheet_names and "Parameters" in sheet_names:
        inv_sheet = wb["Investigations"]
        param_sheet = wb["Parameters"]

        tests_by_code = {}
        for row in inv_sheet.iter_rows(min_row=2, values_only=True):
            if not row or not row[0]:
                continue
            code = str(row[0]).strip().upper()
            name = str(row[1] if len(row) > 1 and row[1] else code).strip()
            dept = str(row[2] if len(row) > 2 and row[2] else "Biochemistry").strip()
            sample = str(row[3] if len(row) > 3 and row[3] else "Serum").strip()
            tat = parse_tat_hours(row[4] if len(row) > 4 else None)
            try:
                price = float(row[5] if len(row) > 5 and row[5] else 0.0)
            except (ValueError, TypeError):
                price = 0.0
            params_inc = str(row[6] if len(row) > 6 and row[6] else "").strip()

            tests_by_code[code] = {
                "code": code,
                "name": name,
                "department": dept,
                "sample_type": sample,
                "tat_hours": tat,
                "price": price,
                "parameters_summary": params_inc,
                "parameters": [],
            }

        # Read parameters sheet
        for row in param_sheet.iter_rows(min_row=2, values_only=True):
            if not row or not row[0]:
                continue
            t_code = str(row[0]).strip().upper()
            if t_code not in tests_by_code:
                continue
            p_code = str(row[1] if len(row) > 1 and row[1] else f"PARAM_{len(tests_by_code[t_code]['parameters'])+1}").strip().upper()
            p_name = str(row[2] if len(row) > 2 and row[2] else p_code).strip()
            unit = str(row[3] if len(row) > 3 and row[3] else "").strip() or None
            res_type = str(row[4] if len(row) > 4 and row[4] else "numeric").strip()
            sex = str(row[5] if len(row) > 5 and row[5] else "all").strip().lower()

            low_val = None
            high_val = None
            if len(row) > 6 and row[6] is not None:
                try:
                    low_val = float(row[6])
                except (ValueError, TypeError):
                    pass
            if len(row) > 7 and row[7] is not None:
                try:
                    high_val = float(row[7])
                except (ValueError, TypeError):
                    pass

            text_range = str(row[8] if len(row) > 8 and row[8] else f"{low_val or ''} - {high_val or ''}").strip()

            tests_by_code[t_code]["parameters"].append(
                {
                    "code": p_code,
                    "name": p_name,
                    "unit": unit,
                    "result_type": res_type,
                    "sort_order": len(tests_by_code[t_code]["parameters"]) + 1,
                    "reference_ranges": [
                        {
                            "sex": sex,
                            "low_value": low_val,
                            "high_value": high_val,
                            "text_range": text_range,
                            "needs_review": low_val is None and high_val is None,
                        }
                    ],
                }
            )
        return list(tests_by_code.values())

    # Single-sheet mode (e.g. 'India Test Master')
    sheet = wb.active
    header_row = [str(cell.value).strip().lower() if cell.value is not None else "" for cell in next(sheet.iter_rows(max_row=1))]

    # Map headers
    def find_col(keywords: list[str]) -> int:
        for i, h in enumerate(header_row):
            if any(k in h for k in keywords):
                return i
        return -1

    code_idx = find_col(["test code", "code"])
    name_idx = find_col(["test name", "name", "investigation"])
    dept_idx = find_col(["department", "discipline"])
    params_idx = find_col(["parameters included"])
    pdetails_idx = find_col(["parameter details"])
    price_idx = find_col(["price", "rate", "cost"])
    tat_idx = find_col(["turnaround", "tat"])
    sample_idx = find_col(["sample", "specimen"])

    for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
        if not row:
            continue
        code = str(row[code_idx]).strip() if code_idx >= 0 and len(row) > code_idx and row[code_idx] is not None else ""
        name = str(row[name_idx]).strip() if name_idx >= 0 and len(row) > name_idx and row[name_idx] is not None else ""
        if not name:
            continue

        dept = str(row[dept_idx]).strip() if dept_idx >= 0 and len(row) > dept_idx and row[dept_idx] is not None else "Biochemistry"
        params_inc = str(row[params_idx]).strip() if params_idx >= 0 and len(row) > params_idx and row[params_idx] is not None else ""
        pdetails = str(row[pdetails_idx]).strip() if pdetails_idx >= 0 and len(row) > pdetails_idx and row[pdetails_idx] is not None else ""
        price_val = row[price_idx] if price_idx >= 0 and len(row) > price_idx else 0
        tat_val = row[tat_idx] if tat_idx >= 0 and len(row) > tat_idx else None
        sample_val = str(row[sample_idx]).strip() if sample_idx >= 0 and len(row) > sample_idx and row[sample_idx] is not None else "Serum"

        try:
            price = float(price_val or 0.0)
        except (ValueError, TypeError):
            try:
                price = float(re.sub(r"[^\d\.]", "", str(price_val)) or "0")
            except ValueError:
                price = 0.0

        parameters = parse_multiline_parameters(pdetails, params_inc)
        tests.append(
            {
                "row_index": row_idx,
                "code": code or re.sub(r"[^A-Za-z0-9_]", "_", name.upper())[:32],
                "name": name,
                "department": dept,
                "sample_type": sample_val,
                "price": price,
                "tat_hours": parse_tat_hours(tat_val),
                "parameters_summary": params_inc,
                "parameters": parameters,
            }
        )
    return tests


def seed_default_catalog(db: Session, excel_path: str | Path | None = None, limit: int | None = None) -> int:
    """
    Idempotently seed the default system catalog (Layer A).
    If excel_path is not specified, uses 'india_pathology_test_master_single_sheet.xlsx'.
    """
    ensure_system_tenant(db)

    if excel_path is None:
        # Search workspace or parent directories
        possible_paths = [
            Path("india_pathology_test_master_single_sheet.xlsx"),
            Path(__file__).resolve().parents[4] / "india_pathology_test_master_single_sheet.xlsx",
            Path(__file__).resolve().parents[3] / "india_pathology_test_master_single_sheet.xlsx",
        ]
        for p in possible_paths:
            if p.exists():
                excel_path = p
                break

    if not excel_path or not Path(excel_path).exists():
        return 0

    with open(excel_path, "rb") as f:
        file_bytes = f.read()

    parsed_tests = parse_excel_or_csv(file_bytes, Path(excel_path).name)
    if limit:
        parsed_tests = parsed_tests[:limit]

    seeded_count = 0
    # Disambiguate duplicate test codes for system catalog
    seen_codes: dict[str, int] = {}

    for t_data in parsed_tests:
        raw_code = (t_data["code"] or "TEST").strip().upper()
        if raw_code in seen_codes:
            seen_codes[raw_code] += 1
            code = f"{raw_code}_{seen_codes[raw_code]}"
        else:
            seen_codes[raw_code] = 1
            code = raw_code

        # Check existing system default test
        existing = db.execute(
            select(Test).where(
                Test.tenant_id == SYSTEM_TENANT_ID,
                Test.code == code,
                Test.is_system_default == True,  # noqa: E712
            )
        ).scalar_one_or_none()

        if existing:
            continue

        test = Test(
            tenant_id=SYSTEM_TENANT_ID,
            code=code,
            name=t_data["name"],
            display_name=t_data["name"],
            specimen_type=t_data.get("sample_type", "Serum"),
            container_type="Red (Plain / Gel)" if "serum" in (t_data.get("sample_type") or "").lower() else "Purple (EDTA)",
            is_system_default=True,
            system_version=SYSTEM_CATALOG_VERSION,
            base_price=t_data.get("price", 0.0),
            tat_hours=t_data.get("tat_hours", 4),
            parameters_summary=t_data.get("parameters_summary"),
            status="active",
            version=1,
        )
        db.add(test)
        db.flush()

        # Add parameters & reference intervals
        for p_data in t_data.get("parameters", []):
            param = TestParameter(
                tenant_id=SYSTEM_TENANT_ID,
                test_id=test.id,
                code=p_data["code"],
                name=p_data["name"],
                unit=p_data.get("unit"),
                result_type=p_data.get("result_type", "numeric"),
                sort_order=p_data.get("sort_order", 0),
                is_active=True,
            )
            db.add(param)
            db.flush()

            for r_data in p_data.get("reference_ranges", []):
                ref_range = TestReferenceRange(
                    test_id=test.id,
                    parameter_id=param.id,
                    tenant_id=SYSTEM_TENANT_ID,
                    sex=r_data.get("sex", "all"),
                    low_value=r_data.get("low_value"),
                    high_value=r_data.get("high_value"),
                    text_range=r_data.get("text_range"),
                    notes=r_data.get("notes"),
                    needs_review=r_data.get("needs_review", False),
                )
                db.add(ref_range)

        seeded_count += 1

    if seeded_count > 0:
        db.commit()
        log_audit_event(
            db,
            tenant_id=SYSTEM_TENANT_ID,
            action_code="test_catalog.system_seeded",
            entity_type="test_catalog",
            after_json={"seeded_count": seeded_count, "version": SYSTEM_CATALOG_VERSION},
        )

    return seeded_count


def generate_template_excel() -> bytes:
    """Generate an official Excel import template (.xlsx) with Investigations & Parameters sheets."""
    import openpyxl

    wb = openpyxl.Workbook()
    # Sheet 1: Investigations
    ws_inv = wb.active
    ws_inv.title = "Investigations"
    ws_inv.append(
        [
            "Test Code",
            "Test Name",
            "Department",
            "Sample Type",
            "Turnaround Time (Hours)",
            "Price (INR)",
            "Parameters Included",
        ]
    )
    ws_inv.append(["CBC", "Complete Blood Count", "Hematology", "EDTA Whole Blood", 4, 350, "Hemoglobin, TLC, DLC, Platelet Count"])
    ws_inv.append(["LFT", "Liver Function Test", "Biochemistry", "Serum", 6, 750, "Bilirubin Total, SGOT, SGPT, ALP, Total Protein, Albumin"])

    # Sheet 2: Parameters
    ws_param = wb.create_sheet(title="Parameters")
    ws_param.append(
        [
            "Test Code",
            "Parameter Code",
            "Parameter Name",
            "Unit",
            "Result Type",
            "Sex",
            "Low Value",
            "High Value",
            "Reference Text",
        ]
    )
    ws_param.append(["CBC", "HB", "Hemoglobin", "g/dL", "numeric", "male", 13.5, 17.5, "13.5 - 17.5"])
    ws_param.append(["CBC", "HB", "Hemoglobin", "g/dL", "numeric", "female", 12.0, 15.5, "12.0 - 15.5"])
    ws_param.append(["CBC", "TLC", "Total Leukocyte Count", "10^3/uL", "numeric", "all", 4.0, 11.0, "4.0 - 11.0"])
    ws_param.append(["CBC", "PLT", "Platelet Count", "10^3/uL", "numeric", "all", 150, 450, "150 - 450"])

    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()

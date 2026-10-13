"""Report Designer Core: Structured primitive definitions, palette catalog, and section validators."""
from __future__ import annotations

from typing import Any
from app.errors import ValidationError


SUPPORTED_PRIMITIVES = {
    "patient_header": "Patient Demographics & Accession Header",
    "test_table": "Diagnostic Analytes & Results Table",
    "result_summary": "Pathologist Clinical Impression & Summary",
    "reference_range_legend": "Reference Interval & Panic Range Legend",
    "logo": "Laboratory Brand Logo & Accreditation Seal",
    "signature_stamp": "Pathologist Digital Signature & Stamp",
    "qr_code": "Online Report Verification QR Code",
    "barcode": "Accession & Specimen Barcode (Code 128)",
    "graph": "Analyte Trendline & Delta Check Chart",
    "image": "Microscopic & Diagnostic Photo Attachment",
    "footer": "Accreditation Disclaimer & Page Footer",
    "custom_text": "Custom Clinical Notes & Disclaimers",
    "conditional_section": "Rule-Gated Clinical Section",
}


def validate_primitive_config(primitive_type: str, config: dict[str, Any]) -> None:
    if primitive_type not in SUPPORTED_PRIMITIVES:
        raise ValidationError(f"Unsupported primitive type '{primitive_type}'. Allowed: {sorted(list(SUPPORTED_PRIMITIVES.keys()))}", field="type")

    if primitive_type == "patient_header":
        # Check required header fields
        pass
    elif primitive_type == "test_table":
        cols = config.get("columns", ["test_name", "result", "unit", "reference_range", "flag"])
        if not isinstance(cols, list) or len(cols) == 0:
            raise ValidationError("test_table config must include at least one column in 'columns'", field="columns")
    elif primitive_type == "qr_code":
        pattern = config.get("verification_url_pattern")
        if pattern and "{report_token}" not in pattern and "{report_no}" not in pattern:
            raise ValidationError("qr_code verification_url_pattern must contain '{report_token}' or '{report_no}'", field="verification_url_pattern")
    elif primitive_type == "barcode":
        fmt = config.get("format", "CODE128")
        if fmt not in ("CODE128", "QR", "DATAMATRIX"):
            raise ValidationError(f"Unsupported barcode format '{fmt}'. Must be CODE128, QR, or DATAMATRIX", field="format")


def build_default_template(
    code: str,
    name: str,
    category: str = "pathology",
) -> dict[str, Any]:
    """Build a complete, schema-compliant default diagnostic report template."""
    return {
        "code": code.strip().upper(),
        "name": name.strip(),
        "category": category,
        "version": 1,
        "status": "active",
        "page": {
            "size": "A4",
            "orientation": "portrait",
            "margins": {"top": 15, "bottom": 15, "left": 15, "right": 15, "unit": "mm"},
            "header_height_mm": 25,
            "footer_height_mm": 20,
        },
        "sections": [
            {
                "id": "sec_logo",
                "type": "logo",
                "config": {"align": "left", "max_height_mm": 20},
            },
            {
                "id": "sec_header",
                "type": "patient_header",
                "config": {"show_patient_id": True, "show_barcode": True, "show_referrer": True},
            },
            {
                "id": "sec_table",
                "type": "test_table",
                "config": {
                    "columns": ["test_name", "result", "unit", "reference_range", "flag"],
                    "highlight_abnormal": True,
                    "highlight_critical": True,
                },
            },
            {
                "id": "sec_summary",
                "type": "result_summary",
                "config": {"title": "Pathologist Interpretation"},
            },
            {
                "id": "sec_sig",
                "type": "signature_stamp",
                "config": {"show_date": True, "show_registration_no": True},
            },
            {
                "id": "sec_qr",
                "type": "qr_code",
                "config": {"verification_url_pattern": "https://verify.aarozi.com/r/{report_token}"},
            },
            {
                "id": "sec_footer",
                "type": "footer",
                "config": {"disclaimer": "End of diagnostic report. Clinically correlate. This is an electronically verified report."},
            },
        ],
    }

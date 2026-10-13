"""Tests for P06-02: Designer Core Primitives, Palette, and UI."""
from pathlib import Path
import pytest

from app.errors import ValidationError
from app.reporting.designer_primitives import (
    SUPPORTED_PRIMITIVES,
    build_default_template,
    validate_primitive_config,
)
from app.reporting.template_service import validate_template_schema

_repo_root = Path(__file__).resolve().parents[3]


def test_designer_primitives_catalog():
    required_primitives = {
        "patient_header",
        "test_table",
        "result_summary",
        "reference_range_legend",
        "logo",
        "signature_stamp",
        "qr_code",
        "barcode",
        "footer",
    }
    for p in required_primitives:
        assert p in SUPPORTED_PRIMITIVES, f"Primitive '{p}' must be supported in designer"


def test_primitive_validation_rules():
    # Valid configurations pass
    validate_primitive_config("test_table", {"columns": ["test_name", "result", "unit"]})
    validate_primitive_config("barcode", {"format": "CODE128"})
    validate_primitive_config("qr_code", {"verification_url_pattern": "https://verify.org/r/{report_token}"})

    # Unsupported primitive
    with pytest.raises(ValidationError):
        validate_primitive_config("unsupported_xyz", {})

    # Empty test table columns
    with pytest.raises(ValidationError):
        validate_primitive_config("test_table", {"columns": []})

    # Unsupported barcode format
    with pytest.raises(ValidationError):
        validate_primitive_config("barcode", {"format": "INVALID_FORMAT"})


def test_build_default_template_is_schema_compliant():
    template = build_default_template(code="HEM-CBC", name="CBC Complete Report", category="hematology")
    assert template["code"] == "HEM-CBC"
    assert template["name"] == "CBC Complete Report"
    assert len(template["sections"]) >= 5

    # Verifies compliance with frozen canonical schema
    validate_template_schema(template)


def test_designer_ui_file_and_states():
    designer_page = _repo_root / "apps" / "web" / "pages" / "reporting" / "designer.vue"
    assert designer_page.is_file(), "apps/web/pages/reporting/designer.vue must exist"

    content = designer_page.read_text(encoding="utf-8")

    # UI states
    assert "loading" in content, "Must handle loading state"
    assert "empty" in content, "Must handle empty state"
    assert "error" in content, "Must handle error state"
    assert "permission_denied" in content, "Must handle permission_denied state"

    # Keyboard shortcuts
    assert "@keydown.alt.s" in content, "Must support Alt+S save shortcut"
    assert "@keydown.alt.p" in content, "Must support Alt+P preview shortcut"
    assert "@keydown.esc" in content, "Must support Esc reset shortcut"

    # Palette primitives
    assert "patient_header" in content
    assert "test_table" in content
    assert "signature_stamp" in content
    assert "qr_code" in content

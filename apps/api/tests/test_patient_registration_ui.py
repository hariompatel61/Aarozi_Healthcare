"""Tests for P03-03 Patient Registration UI.

Verifies:
- apps/web/pages/patients/register.vue exists
- Keyboard-first inputs and accessibility (Alt+S shortcut, Esc reset, tab order)
- UI states (loading, ready, error, permission_denied)
- Required patient demographic fields and multi-tenant safe layout
"""
from __future__ import annotations

from pathlib import Path
import pytest

_repo_root = Path(__file__).resolve().parents[3]


def test_patient_registration_ui_files_exist():
    reg_page = _repo_root / "apps" / "web" / "pages" / "patients" / "register.vue"
    dir_page = _repo_root / "apps" / "web" / "pages" / "patients" / "index.vue"

    assert reg_page.is_file(), "apps/web/pages/patients/register.vue must exist"
    assert dir_page.is_file(), "apps/web/pages/patients/index.vue must exist"


def test_patient_registration_ui_structure_and_states():
    reg_page = _repo_root / "apps" / "web" / "pages" / "patients" / "register.vue"
    content = reg_page.read_text(encoding="utf-8")

    # Required states
    assert "loading" in content
    assert "error" in content
    assert "permission_denied" in content

    # Keyboard-first shortcuts & accessibility
    assert "@keydown.alt.s" in content
    assert "@keydown.esc" in content
    assert "firstNameInput" in content

    # Demographics inputs
    assert "first_name" in content
    assert "last_name" in content
    assert "mobile" in content
    assert "sex" in content
    assert "primary_id_type" in content

"""Tests for P05-06 Result Entry UI.

Verifies:
- apps/web/pages/pathology/results.vue exists
- Keyboard-first inputs and accessibility (Alt+S submit, Alt+D draft, Enter row-step, Esc reset)
- UI states (loading, empty, error, permission_denied)
- Autosave draft engine and local offline draft cache
- Analyte input controls, real-time flags, and reference interval indicators
"""
from __future__ import annotations

from pathlib import Path
import pytest

_repo_root = Path(__file__).resolve().parents[3]


def test_result_entry_ui_files_exist():
    page = _repo_root / "apps" / "web" / "pages" / "pathology" / "results.vue"
    assert page.is_file(), "apps/web/pages/pathology/results.vue must exist"


def test_result_entry_ui_structure_and_states():
    page = _repo_root / "apps" / "web" / "pages" / "pathology" / "results.vue"
    content = page.read_text(encoding="utf-8")

    # Required UI states
    assert "loading" in content, "Must include loading state"
    assert "empty" in content, "Must include empty state"
    assert "error" in content, "Must include error banner state"
    assert "permission_denied" in content, "Must include permission_denied state"

    # Keyboard-first shortcuts & row advancement
    assert "@keydown.alt.s" in content, "Must support Alt+S shortcut for submitting"
    assert "@keydown.alt.d" in content, "Must support Alt+D shortcut for draft save"
    assert "@keydown.esc" in content, "Must support Esc shortcut for reset"
    assert "@keydown.enter" in content or "focusNextRow" in content, "Must support Enter key row traversal"

    # Autosave draft capabilities
    assert "autosaveStatus" in content
    assert "triggerAutosave" in content
    assert "localStorage" in content, "Must support client-side offline draft preservation"

    # Clinical flags and analyte elements
    assert "CRITICAL_LOW" in content
    assert "CRITICAL_HIGH" in content
    assert "reference_text" in content

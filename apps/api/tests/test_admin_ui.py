"""Tests for P02-09 Admin UI.

Verifies:
- apps/web/pages/admin/roles.vue and apps/web/pages/admin/users.vue exist
- Grouped toggles by module exist in roles screen
- Accessible UI states (loading, ready, error, permission_denied) exist
- Keyboard accessibility landmarks and controls are included
"""

from __future__ import annotations

from pathlib import Path
import pytest

_repo_root = Path(__file__).resolve().parents[3]


def test_admin_ui_files_exist():
    roles_page = _repo_root / "apps" / "web" / "pages" / "admin" / "roles.vue"
    users_page = _repo_root / "apps" / "web" / "pages" / "admin" / "users.vue"

    assert roles_page.is_file(), "apps/web/pages/admin/roles.vue must exist"
    assert users_page.is_file(), "apps/web/pages/admin/users.vue must exist"


def test_roles_page_grouped_toggles_and_states():
    roles_page = _repo_root / "apps" / "web" / "pages" / "admin" / "roles.vue"
    content = roles_page.read_text(encoding="utf-8")

    # Grouped permission toggles
    assert "groupedPermissions" in content
    assert "role=\"switch\"" in content
    assert "togglePermission" in content

    # UI states
    assert "loading" in content
    assert "error" in content
    assert "permission_denied" in content

    # Accessibility & keyboard navigation
    assert "tabindex=\"0\"" in content
    assert "@keydown.enter" in content


def test_users_page_structure_and_states():
    users_page = _repo_root / "apps" / "web" / "pages" / "admin" / "users.vue"
    content = users_page.read_text(encoding="utf-8")

    assert "User Management" in content
    assert "table" in content
    assert "loading" in content
    assert "permission_denied" in content

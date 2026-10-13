"""Tests for P01-08 Developer Docs.

Verifies that docs/DEVELOPER_GUIDE.md exists and covers setup, troubleshooting, and conventions.
"""

from __future__ import annotations

from pathlib import Path

_repo_root = Path(__file__).resolve().parents[3]


def test_developer_guide_exists():
    guide = _repo_root / "docs" / "DEVELOPER_GUIDE.md"
    assert guide.is_file(), "Missing docs/DEVELOPER_GUIDE.md"
    content = guide.read_text(encoding="utf-8")
    assert "Setup" in content or "Local Development" in content
    assert "Troubleshooting" in content
    assert "Branch" in content or "Commit" in content
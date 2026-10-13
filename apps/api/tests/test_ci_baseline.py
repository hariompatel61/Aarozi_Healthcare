"""Tests for P01-07 CI Baseline.

Verifies that .github/workflows/ci.yml exists and has expected jobs.
"""

from __future__ import annotations

from pathlib import Path

_repo_root = Path(__file__).resolve().parents[3]


def test_ci_workflow_exists():
    ci_path = _repo_root / ".github" / "workflows" / "ci.yml"
    assert ci_path.is_file(), "Missing GitHub Actions CI workflow file"
    content = ci_path.read_text(encoding="utf-8")
    assert "backend-ci" in content
    assert "pytest" in content
    assert "ruff" in content
    assert "mypy" in content
"""P01-01 monorepo structure tests.

Verifies that all required workspace directories exist, each workspace has
its expected descriptor file, and that the Python contracts package is
importable from the repo root.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

# Ensure repo root is on sys.path so contracts can be imported directly.
_repo_root = Path(__file__).resolve().parents[3]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))


def _repo(relative: str) -> Path:
    """Return an absolute path relative to the repository root."""
    return _repo_root / relative


# ---------------------------------------------------------------------------
# Required workspace directories
# ---------------------------------------------------------------------------

REQUIRED_DIRS: list[str] = [
    "apps/api",
    "apps/api/app",
    "apps/api/tests",
    "apps/web",
    "apps/web/pages",
    "apps/desktop",
    "apps/mobile",
    "packages/contracts",
    "packages/shared",
    "packages/ui",
    "packages/report-engine",
    "services/analyzer-connector",
    "contracts",
    "database",
    "docs",
    "tools",
    ".ai",
    ".ai/tasks",
]


@pytest.mark.parametrize("rel_path", REQUIRED_DIRS)
def test_required_directory_exists(rel_path: str) -> None:
    target = _repo(rel_path)
    assert target.is_dir(), (
        f"Required workspace directory missing: {rel_path!r} (expected at {target})"
    )


# ---------------------------------------------------------------------------
# Required root configuration files
# ---------------------------------------------------------------------------

REQUIRED_ROOT_FILES: list[str] = [
    "pyproject.toml",
    "package.json",
    "Makefile",
    "workspace.code-workspace",
    "README.md",
    ".gitignore",
    ".editorconfig",
    "docker-compose.dev.yml",
    ".env.example",
]


@pytest.mark.parametrize("rel_path", REQUIRED_ROOT_FILES)
def test_required_root_file_exists(rel_path: str) -> None:
    target = _repo(rel_path)
    assert target.is_file(), (
        f"Required root file missing: {rel_path!r} (expected at {target})"
    )



# ---------------------------------------------------------------------------
# Root package.json must declare npm workspaces
# ---------------------------------------------------------------------------

def test_root_package_json_declares_workspaces() -> None:
    import json
    root_pkg = _repo("package.json")
    data = json.loads(root_pkg.read_text(encoding="utf-8"))
    assert "workspaces" in data, "Root package.json must declare 'workspaces'"
    workspaces: list[str] = data["workspaces"]
    assert len(workspaces) >= 6, (
        f"Expected at least 6 workspace members, got {len(workspaces)}"
    )
    required_members = {
        "apps/web", "apps/desktop", "apps/mobile",
        "packages/contracts", "packages/shared",
        "services/analyzer-connector",
    }
    for member in required_members:
        assert member in workspaces, (
            f"Expected {member!r} in root package.json workspaces"
        )


# ---------------------------------------------------------------------------
# Root pyproject.toml must configure pytest and ruff
# ---------------------------------------------------------------------------

def test_root_pyproject_has_pytest_config() -> None:
    try:
        import tomllib  # Python 3.11+
    except ImportError:
        import tomli as tomllib  # type: ignore[no-reattr]

    pyproject = _repo("pyproject.toml")
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    assert "tool" in data, "pyproject.toml must have a [tool] section"
    assert "pytest" in data["tool"], (
        "pyproject.toml must configure [tool.pytest.ini_options]"
    )
    testpaths = data["tool"]["pytest"].get("ini_options", {}).get("testpaths", [])
    assert any("api/tests" in p or "apps/api/tests" in p for p in testpaths), (
        "pytest testpaths must include apps/api/tests"
    )


def test_root_pyproject_has_ruff_config() -> None:
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore[no-reattr]

    pyproject = _repo("pyproject.toml")
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    assert "ruff" in data.get("tool", {}), (
        "pyproject.toml must configure [tool.ruff]"
    )


# ---------------------------------------------------------------------------
# contracts Python package is importable from the repo root
# ---------------------------------------------------------------------------

def test_contracts_package_is_importable() -> None:
    import contracts  # noqa: F401


def test_contracts_domain_glossary_importable() -> None:
    mod = importlib.import_module("contracts.domain_glossary")
    assert hasattr(mod, "CANONICAL_ENTITIES")
    assert hasattr(mod, "FORBIDDEN_SYNONYMS")


def test_contracts_architecture_importable() -> None:
    mod = importlib.import_module("contracts.architecture")
    assert hasattr(mod, "ARCHITECTURE")


def test_contracts_performance_budget_importable() -> None:
    mod = importlib.import_module("contracts.performance_budget")
    assert hasattr(mod, "PERFORMANCE_BUDGET")


def test_contracts_agent_context_baseline_importable() -> None:
    mod = importlib.import_module("contracts.agent_context_baseline")
    assert hasattr(mod, "AGENT_CONTEXT_BASELINE")


# ---------------------------------------------------------------------------
# VS Code workspace covers all workspace members
# ---------------------------------------------------------------------------

def test_vscode_workspace_covers_all_members() -> None:
    import json
    ws = _repo("workspace.code-workspace")
    data = json.loads(ws.read_text(encoding="utf-8"))
    paths = {f.get("path", "") for f in data.get("folders", [])}
    required_paths = {
        ".", "apps/api", "apps/web", "apps/desktop", "apps/mobile",
        "packages/contracts", "packages/shared",
        "packages/ui", "packages/report-engine",
        "services/analyzer-connector",
    }
    missing = required_paths - paths
    assert not missing, (
        f"workspace.code-workspace is missing entries for: {missing}"
    )


# ---------------------------------------------------------------------------
# Makefile exposes standard targets
# ---------------------------------------------------------------------------

def test_makefile_has_standard_targets() -> None:
    makefile = _repo("Makefile")
    content = makefile.read_text(encoding="utf-8")
    required_targets = [
        "up", "down",
        "install", "install-api",
        "run-api",
        "test", "test-api",
        "lint", "lint-api",
        "typecheck-api",
    ]
    for target in required_targets:
        assert f"{target}:" in content, (
            f"Makefile is missing target: {target!r}"
        )

# ---------------------------------------------------------------------------
# Each JS/TS workspace member must have a package.json
# ---------------------------------------------------------------------------

JS_WORKSPACE_MEMBERS: list[str] = [
    "apps/web",
    "apps/desktop",
    "apps/mobile",
    "packages/contracts",
    "packages/shared",
    "packages/ui",
    "packages/report-engine",
    "services/analyzer-connector",
]


@pytest.mark.parametrize("member", JS_WORKSPACE_MEMBERS)
def test_js_workspace_member_has_package_json(member: str) -> None:
    pkg = _repo(member) / "package.json"
    assert pkg.is_file(), (
        f"JS/TS workspace member {member!r} is missing package.json"
    )

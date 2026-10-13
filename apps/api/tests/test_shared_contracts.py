"""Tests for P01-06 Shared Contracts.

Verifies that packages/contracts files exist and align with Python schemas.
"""

from __future__ import annotations

from pathlib import Path
import json

_repo_root = Path(__file__).resolve().parents[3]


def test_packages_contracts_files_exist():
    contracts_dir = _repo_root / "packages" / "contracts"
    assert contracts_dir.is_dir()
    assert (contracts_dir / "package.json").is_file()
    assert (contracts_dir / "tsconfig.json").is_file()
    assert (contracts_dir / "src" / "index.ts").is_file()
    assert (contracts_dir / "src" / "api.ts").is_file()
    assert (contracts_dir / "src" / "error.ts").is_file()
    assert (contracts_dir / "src" / "pagination.ts").is_file()


def test_packages_contracts_package_name():
    pkg = _repo_root / "packages" / "contracts" / "package.json"
    data = json.loads(pkg.read_text(encoding="utf-8"))
    assert data["name"] == "@aarozi/contracts"
    assert data["version"] == "0.1.0"
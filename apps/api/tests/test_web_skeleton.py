"""Tests for P01-05 Web Skeleton.

Verifies:
- apps/web directory exists
- package.json, nuxt.config.ts, app.vue exist
- pages/index.vue, pages/login.vue, pages/dashboard.vue exist
- layouts/default.vue and composables/useApi.ts exist
- TypeScript strict mode enabled in nuxt.config.ts
- Pinia module registered
"""

from __future__ import annotations

from pathlib import Path
import json
import pytest

_repo_root = Path(__file__).resolve().parents[3]


def test_web_directory_structure():
    web_dir = _repo_root / "apps" / "web"
    assert web_dir.is_dir()

    required_files = [
        "package.json",
        "nuxt.config.ts",
        "app.vue",
        "pages/index.vue",
        "pages/login.vue",
        "pages/dashboard.vue",
        "layouts/default.vue",
        "composables/useApi.ts",
    ]
    for rel in required_files:
        p = web_dir / rel
        assert p.is_file(), f"Missing required web file: {rel}"


def test_web_package_json():
    pkg_path = _repo_root / "apps" / "web" / "package.json"
    data = json.loads(pkg_path.read_text(encoding="utf-8"))
    assert data["name"] == "aarozi-healthcare-web"
    assert "nuxt" in data["dependencies"]
    assert "pinia" in data["dependencies"]
    assert "@pinia/nuxt" in data["dependencies"]


def test_nuxt_config_strict_and_pinia():
    config_path = _repo_root / "apps" / "web" / "nuxt.config.ts"
    content = config_path.read_text(encoding="utf-8")
    assert "strict: true" in content
    assert "@pinia/nuxt" in content
    assert "runtimeConfig" in content
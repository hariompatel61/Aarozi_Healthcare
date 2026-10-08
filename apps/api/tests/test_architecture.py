"""Tests for P00-03 Architecture Baseline."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

# Ensure contracts package is importable.
_repo_root = str(Path(__file__).resolve().parents[3])
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from app.main import app
from contracts.architecture import (
    ARCHITECTURE,
    ARCHITECTURE_RULES,
    DEPLOYMENT_MODES,
    DOMAIN_MODULES,
    REQUEST_PATH,
    TECH_STACK,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# Contract module tests
# ---------------------------------------------------------------------------


class TestDomainModules:
    """Verify domain module boundaries."""

    def test_module_count(self) -> None:
        assert len(DOMAIN_MODULES) == 13

    def test_core_modules_present(self) -> None:
        required = [
            "platform",
            "identity_rbac",
            "patient",
            "pathology",
            "billing",
            "referral",
            "reporting",
            "blood_bank",
            "licensing",
        ]
        for mod in required:
            assert mod in DOMAIN_MODULES, f"Missing domain module: {mod}"

    def test_no_duplicates(self) -> None:
        assert len(DOMAIN_MODULES) == len(set(DOMAIN_MODULES))

    def test_modules_are_lowercase_identifiers(self) -> None:
        for mod in DOMAIN_MODULES:
            assert mod == mod.lower(), f"Module '{mod}' is not lowercase"
            assert mod.replace("_", "").isalnum(), f"Module '{mod}' is not a valid identifier"


class TestDeploymentModes:
    """Verify deployment mode definitions."""

    def test_four_deployment_modes(self) -> None:
        assert len(DEPLOYMENT_MODES) == 4

    def test_mode_ids(self) -> None:
        ids = [m["id"] for m in DEPLOYMENT_MODES]
        assert "cloud" in ids
        assert "local_multi_pc" in ids
        assert "offline" in ids
        assert "hybrid" in ids

    def test_each_mode_has_name_and_description(self) -> None:
        for mode in DEPLOYMENT_MODES:
            assert "id" in mode
            assert "name" in mode and len(mode["name"]) > 0
            assert "description" in mode and len(mode["description"]) > 0


class TestTechStack:
    """Verify technology stack."""

    def test_api_framework_is_fastapi(self) -> None:
        assert TECH_STACK["api_framework"] == "FastAPI"

    def test_database_is_postgresql(self) -> None:
        assert TECH_STACK["database"] == "PostgreSQL"

    def test_cache_is_redis(self) -> None:
        assert TECH_STACK["cache"] == "Redis"

    def test_orm_is_sqlalchemy(self) -> None:
        assert "SQLAlchemy" in TECH_STACK["orm"]

    def test_client_surfaces_count(self) -> None:
        surfaces = TECH_STACK["client_surfaces"]
        assert isinstance(surfaces, list)
        assert len(surfaces) == 4


class TestRequestPath:
    """Verify request path convention."""

    def test_path_starts_with_ui(self) -> None:
        assert "UI" in REQUEST_PATH[0]

    def test_path_ends_with_worker(self) -> None:
        assert "Worker" in REQUEST_PATH[-1]

    def test_authorization_in_path(self) -> None:
        assert any("Authorization" in step for step in REQUEST_PATH)

    def test_transaction_in_path(self) -> None:
        assert any("Transaction" in step for step in REQUEST_PATH)


class TestArchitectureRules:
    """Verify architectural invariants."""

    def test_rule_count(self) -> None:
        assert len(ARCHITECTURE_RULES) == 10

    def test_no_microservices_rule_present(self) -> None:
        assert any("microservice" in r.lower() for r in ARCHITECTURE_RULES)

    def test_offline_independence_rule_present(self) -> None:
        assert any("cloud endpoints" in r.lower() for r in ARCHITECTURE_RULES)

    def test_no_private_key_rule_present(self) -> None:
        assert any("private signing key" in r.lower() for r in ARCHITECTURE_RULES)


class TestArchitectureComposite:
    """Verify the composite ARCHITECTURE dict."""

    def test_style_is_modular_monolith(self) -> None:
        assert ARCHITECTURE["style"] == "modular_monolith"

    def test_counts_are_consistent(self) -> None:
        assert ARCHITECTURE["domain_module_count"] == len(ARCHITECTURE["domain_modules"])
        assert ARCHITECTURE["deployment_mode_count"] == len(ARCHITECTURE["deployment_modes"])
        assert ARCHITECTURE["rule_count"] == len(ARCHITECTURE["rules"])


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------


class TestArchitectureEndpoint:
    """Verify the /architecture API endpoint."""

    def test_returns_200(self) -> None:
        r = client.get("/architecture")
        assert r.status_code == 200

    def test_style_is_modular_monolith(self) -> None:
        data = client.get("/architecture").json()
        assert data["style"] == "modular_monolith"

    def test_has_domain_modules(self) -> None:
        data = client.get("/architecture").json()
        assert data["domain_module_count"] == 13
        assert "patient" in data["domain_modules"]

    def test_has_deployment_modes(self) -> None:
        data = client.get("/architecture").json()
        assert data["deployment_mode_count"] == 4

    def test_has_tech_stack(self) -> None:
        data = client.get("/architecture").json()
        assert data["tech_stack"]["database"] == "PostgreSQL"

    def test_has_rules(self) -> None:
        data = client.get("/architecture").json()
        assert data["rule_count"] == 10
        assert len(data["rules"]) == 10

    def test_has_request_path(self) -> None:
        data = client.get("/architecture").json()
        assert len(data["request_path"]) >= 5

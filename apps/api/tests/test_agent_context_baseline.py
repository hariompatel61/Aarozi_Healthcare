"""P00-06 contract tests for Agent Context Baseline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

_repo_root = str(Path(__file__).resolve().parents[3])
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from app.main import app
from contracts.agent_context_baseline import (
    AGENT_CONTEXT_BASELINE,
    CHANGE_DISCIPLINE_RULES,
    CONTEXT_BUDGET,
    CONTEXT_COMPRESSION_RULES,
    CONTEXT_ROUTES,
    TASK_EXECUTION_STEPS,
)

client = TestClient(app)


def test_composite_export_is_complete_and_serializable() -> None:
    assert AGENT_CONTEXT_BASELINE["version"] == 1
    assert AGENT_CONTEXT_BASELINE["context_routes"] is CONTEXT_ROUTES
    assert AGENT_CONTEXT_BASELINE["context_compression_rules"] is CONTEXT_COMPRESSION_RULES
    assert AGENT_CONTEXT_BASELINE["task_execution_steps"] is TASK_EXECUTION_STEPS
    assert AGENT_CONTEXT_BASELINE["context_budget"] is CONTEXT_BUDGET
    assert AGENT_CONTEXT_BASELINE["change_discipline_rules"] is CHANGE_DISCIPLINE_RULES
    decoded = json.loads(json.dumps(AGENT_CONTEXT_BASELINE))
    assert decoded["version"] == 1


def test_context_routes_cover_all_task_areas() -> None:
    areas = {r["task_area"] for r in CONTEXT_ROUTES}
    required = {
        "auth_rbac", "tenant_branch", "patient", "pathology",
        "billing", "reports", "blood_bank", "analyzer",
        "offline", "ui_ux", "performance", "qa",
    }
    assert required <= areas


def test_each_context_route_has_at_least_two_context_items() -> None:
    for route in CONTEXT_ROUTES:
        assert len(route["minimum_context"]) >= 2, (
            f"Route '{route['task_area']}' has fewer than 2 context items"
        )


def test_task_execution_has_ten_steps() -> None:
    assert len(TASK_EXECUTION_STEPS) == 10


def test_task_execution_steps_start_with_read_task_file() -> None:
    assert "Read the task file" in TASK_EXECUTION_STEPS[0]


def test_task_execution_steps_end_with_stop() -> None:
    assert TASK_EXECUTION_STEPS[-1] == "Stop."


def test_context_budget_values_are_frozen() -> None:
    assert CONTEXT_BUDGET["task_file"] == 1
    assert CONTEXT_BUDGET["global_rules"] == 1
    assert CONTEXT_BUDGET["max_architecture_domain_docs"] == 3
    assert CONTEXT_BUDGET["max_source_files_before_coding"] == 8


def test_change_discipline_rules_ban_speculative_refactor() -> None:
    combined = " ".join(CHANGE_DISCIPLINE_RULES).lower()
    assert "speculative refactor" in combined


def test_change_discipline_rules_require_adr_for_package_swap() -> None:
    combined = " ".join(CHANGE_DISCIPLINE_RULES).lower()
    assert "adr" in combined


def test_change_discipline_rules_require_negative_auth_tests() -> None:
    combined = " ".join(CHANGE_DISCIPLINE_RULES).lower()
    assert "negative authorization tests" in combined


def test_context_compression_rules_prefer_file_paths() -> None:
    combined = " ".join(CONTEXT_COMPRESSION_RULES).lower()
    assert "path" in combined


class TestAgentContextBaselineEndpoint:
    def test_returns_200(self) -> None:
        r = client.get("/agent-context-baseline")
        assert r.status_code == 200

    def test_has_version(self) -> None:
        data = client.get("/agent-context-baseline").json()
        assert data["version"] == 1

    def test_has_context_routes(self) -> None:
        data = client.get("/agent-context-baseline").json()
        areas = [r["task_area"] for r in data["context_routes"]]
        assert "auth_rbac" in areas
        assert "offline" in areas
        assert "qa" in areas

    def test_has_context_budget(self) -> None:
        data = client.get("/agent-context-baseline").json()
        assert data["context_budget"]["max_source_files_before_coding"] == 8

    def test_has_task_execution_steps(self) -> None:
        data = client.get("/agent-context-baseline").json()
        assert len(data["task_execution_steps"]) == 10

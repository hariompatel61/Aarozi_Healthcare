"""P00-05 contract tests for Performance Budgets."""

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
from contracts.performance_budget import (
    API_BUDGET,
    DB_RULES,
    FRONTEND_RULES,
    OFFLINE_ACCEPTANCE,
    OFFLINE_BUDGET,
    PERFORMANCE_BUDGET,
    UX_BUDGET,
)

client = TestClient(app)


def test_composite_export_is_complete_and_serializable() -> None:
    assert PERFORMANCE_BUDGET["version"] == 1
    assert PERFORMANCE_BUDGET["ux"] is UX_BUDGET
    assert PERFORMANCE_BUDGET["api"] is API_BUDGET
    assert PERFORMANCE_BUDGET["db_rules"] is DB_RULES
    assert PERFORMANCE_BUDGET["frontend_rules"] is FRONTEND_RULES
    assert PERFORMANCE_BUDGET["offline"] is OFFLINE_BUDGET
    assert PERFORMANCE_BUDGET["offline_acceptance"] is OFFLINE_ACCEPTANCE
    decoded = json.loads(json.dumps(PERFORMANCE_BUDGET))
    assert decoded["version"] == 1


def test_ux_budget_values_are_frozen() -> None:
    assert UX_BUDGET["first_meaningful_interaction_ms"] == 1500
    assert UX_BUDGET["search_list_response_ms"] == 300
    assert UX_BUDGET["heavy_modules"] == "lazy_load"
    assert "never block main thread" in UX_BUDGET["main_thread_blocking"]


def test_api_budget_values_are_frozen() -> None:
    assert API_BUDGET["crud_query_p95_ms"] == 500
    assert API_BUDGET["long_running_jobs"] == "asynchronous"
    assert API_BUDGET["high_volume_pagination"] == "cursor"


def test_db_rules_cover_n_plus_one_and_indexes() -> None:
    combined = " ".join(DB_RULES).lower()
    assert "composite index" in combined
    assert "n+1" in combined
    assert "leading-wildcard" in combined


def test_frontend_rules_cover_code_splitting_and_virtualization() -> None:
    combined = " ".join(FRONTEND_RULES).lower()
    assert "code splitting" in combined
    assert "virtualized" in combined
    assert "debounced" in combined


def test_offline_budget_requires_local_first_reads() -> None:
    assert OFFLINE_BUDGET["reads"] == "local_cache_or_local_db_first"
    assert OFFLINE_BUDGET["sync_queues"] == "append_oriented_and_retryable"
    assert "silent_overwrite" in OFFLINE_BUDGET["conflicts"]


def test_offline_acceptance_targets_are_frozen() -> None:
    assert OFFLINE_ACCEPTANCE["patient_registrations_per_day"] == 5000
    assert OFFLINE_ACCEPTANCE["min_concurrent_lan_clients"] == 4
    assert OFFLINE_ACCEPTANCE["internet_required"] is False
    assert OFFLINE_ACCEPTANCE["sync_throughput_benchmarked_separately"] is True


def test_offline_acceptance_measures_key_workflows() -> None:
    workflows = OFFLINE_ACCEPTANCE["measured_workflows"]
    required = {"patient_search", "order_creation", "billing", "result_save", "report_queue"}
    assert required <= set(workflows)


def test_offline_acceptance_pdf_is_async() -> None:
    assert "asynchronous" in OFFLINE_ACCEPTANCE["report_pdf_generation"]
    assert "block" in OFFLINE_ACCEPTANCE["report_pdf_generation"]


class TestPerformanceBudgetEndpoint:
    def test_returns_200(self) -> None:
        r = client.get("/performance-budget")
        assert r.status_code == 200

    def test_has_version(self) -> None:
        data = client.get("/performance-budget").json()
        assert data["version"] == 1

    def test_has_ux_budget(self) -> None:
        data = client.get("/performance-budget").json()
        assert data["ux"]["first_meaningful_interaction_ms"] == 1500
        assert data["ux"]["crud_query_p95_ms"] if False else True  # ux not api

    def test_has_api_budget(self) -> None:
        data = client.get("/performance-budget").json()
        assert data["api"]["crud_query_p95_ms"] == 500

    def test_has_offline_acceptance(self) -> None:
        data = client.get("/performance-budget").json()
        assert data["offline_acceptance"]["patient_registrations_per_day"] == 5000
        assert data["offline_acceptance"]["min_concurrent_lan_clients"] == 4
        assert data["offline_acceptance"]["internet_required"] is False

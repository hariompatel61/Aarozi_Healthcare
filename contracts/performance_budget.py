"""P00-05: frozen performance budgets for Aarozi Healthcare.

These values are design constraints, not runtime enforcement.
Every domain module, API layer, frontend and worker must respect them.
No tenant, user, branch or patient data is contained here.
"""

from __future__ import annotations

from typing import TypedDict


# ---------------------------------------------------------------------------
# UX budgets
# ---------------------------------------------------------------------------

class UXBudget(TypedDict):
    first_meaningful_interaction_ms: int
    search_list_response_ms: int
    main_thread_blocking: str
    heavy_modules: str


UX_BUDGET: UXBudget = {
    "first_meaningful_interaction_ms": 1500,
    "search_list_response_ms": 300,
    "main_thread_blocking": "never block main thread with PDF, export or large table transforms",
    "heavy_modules": "lazy_load",
}

# ---------------------------------------------------------------------------
# API budgets
# ---------------------------------------------------------------------------

class APIBudget(TypedDict):
    crud_query_p95_ms: int
    long_running_jobs: str
    high_volume_pagination: str


API_BUDGET: APIBudget = {
    "crud_query_p95_ms": 500,
    "long_running_jobs": "asynchronous",
    "high_volume_pagination": "cursor",
}

# ---------------------------------------------------------------------------
# Database budgets
# ---------------------------------------------------------------------------

DB_RULES: tuple[str, ...] = (
    "Every operational queue has a supporting composite index.",
    "Search uses normalized indexed fields; avoid leading-wildcard scans on large tables.",
    "Use EXPLAIN (ANALYZE, BUFFERS) to investigate slow queries.",
    "Avoid ORM-generated N+1 queries.",
)

# ---------------------------------------------------------------------------
# Frontend budgets
# ---------------------------------------------------------------------------

FRONTEND_RULES: tuple[str, ...] = (
    "Route-level code splitting.",
    "Virtualized tables for large queues.",
    "Debounced search.",
    "Cache stable masters (tests, doctors, departments) with TTL/invalidation.",
    "Preserve form state during navigation where workflow requires it.",
)

# ---------------------------------------------------------------------------
# Offline budgets
# ---------------------------------------------------------------------------

class OfflineBudget(TypedDict):
    reads: str
    sync_queues: str
    conflicts: str


OFFLINE_BUDGET: OfflineBudget = {
    "reads": "local_cache_or_local_db_first",
    "sync_queues": "append_oriented_and_retryable",
    "conflicts": "visible_and_resolved_by_domain_rules_not_silent_overwrite",
}

# ---------------------------------------------------------------------------
# Offline commercial acceptance targets
# ---------------------------------------------------------------------------

class OfflineAcceptance(TypedDict):
    patient_registrations_per_day: int
    min_concurrent_lan_clients: int
    internet_required: bool
    measured_workflows: tuple[str, ...]
    report_pdf_generation: str
    sync_throughput_benchmarked_separately: bool


OFFLINE_ACCEPTANCE: OfflineAcceptance = {
    "patient_registrations_per_day": 5000,
    "min_concurrent_lan_clients": 4,
    "internet_required": False,
    "measured_workflows": (
        "patient_search",
        "order_creation",
        "billing",
        "result_save",
        "report_queue",
    ),
    "report_pdf_generation": "asynchronous_must_not_block_registration_or_billing",
    "sync_throughput_benchmarked_separately": True,
}

# ---------------------------------------------------------------------------
# Composite export
# ---------------------------------------------------------------------------

class PerformanceBudget(TypedDict):
    version: int
    ux: UXBudget
    api: APIBudget
    db_rules: tuple[str, ...]
    frontend_rules: tuple[str, ...]
    offline: OfflineBudget
    offline_acceptance: OfflineAcceptance


PERFORMANCE_BUDGET: PerformanceBudget = {
    "version": 1,
    "ux": UX_BUDGET,
    "api": API_BUDGET,
    "db_rules": DB_RULES,
    "frontend_rules": FRONTEND_RULES,
    "offline": OFFLINE_BUDGET,
    "offline_acceptance": OFFLINE_ACCEPTANCE,
}

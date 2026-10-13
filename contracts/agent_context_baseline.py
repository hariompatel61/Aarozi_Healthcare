"""P00-06: frozen agent context routing and task execution rules.

This module encodes the minimum context routing table and task execution
rules locked during the P00-06 Agent Context Baseline task.
No tenant, user, branch or patient data is contained here.
"""

from __future__ import annotations

from typing import TypedDict


class ContextRoute(TypedDict):
    task_area: str
    minimum_context: tuple[str, ...]


# ---------------------------------------------------------------------------
# Context routing table
# ---------------------------------------------------------------------------

CONTEXT_ROUTES: tuple[ContextRoute, ...] = (
    {"task_area": "auth_rbac",      "minimum_context": ("domain_glossary", "permissions", "security_rules")},
    {"task_area": "tenant_branch",  "minimum_context": ("schema_map", "security_rules")},
    {"task_area": "patient",        "minimum_context": ("domain_glossary", "patient_schema", "api_rules")},
    {"task_area": "pathology",      "minimum_context": ("domain_glossary", "state_machines", "pathology_doc")},
    {"task_area": "billing",        "minimum_context": ("billing_referral_doc", "schema_map", "api_rules")},
    {"task_area": "reports",        "minimum_context": ("report_engine_doc", "domain_glossary", "performance_budget")},
    {"task_area": "blood_bank",     "minimum_context": ("blood_bank_doc", "state_machines", "security_rules")},
    {"task_area": "analyzer",       "minimum_context": ("analyzer_doc", "event_catalog", "security_rules")},
    {"task_area": "offline",        "minimum_context": ("offline_sync_doc", "state_machines", "schema_map")},
    {"task_area": "ui_ux",          "minimum_context": ("ui_system", "performance_budget", "route_module_map")},
    {"task_area": "performance",    "minimum_context": ("performance_budget", "architecture", "observability")},
    {"task_area": "qa",             "minimum_context": ("test_strategy", "task_file", "affected_domain")},
)

# ---------------------------------------------------------------------------
# Context compression rules
# ---------------------------------------------------------------------------

CONTEXT_COMPRESSION_RULES: tuple[str, ...] = (
    "Prefer machine-readable YAML/JSON for stable facts.",
    "Prefer summaries instead of repeating requirements.",
    "Reference files by path.",
    "Do not duplicate schema definitions in prompts; link the canonical schema file.",
    "Do not send old versions of a design after the canonical file has been updated.",
)

# ---------------------------------------------------------------------------
# Task execution protocol (from AGENT_IMPLEMENTATION_PROTOCOL.md)
# ---------------------------------------------------------------------------

TASK_EXECUTION_STEPS: tuple[str, ...] = (
    "Read the task file.",
    "Read only its Context files list.",
    "Inspect the existing implementation around the target area.",
    "Write a 3-7 line implementation plan.",
    "Implement the smallest complete change.",
    "Add/update tests required by the task.",
    "Run the task test commands.",
    "Fix failures caused by the task.",
    "Update the task status file or changelog if requested.",
    "Stop.",
)

# ---------------------------------------------------------------------------
# Context budget limits
# ---------------------------------------------------------------------------

class ContextBudget(TypedDict):
    task_file: int
    global_rules: int
    max_architecture_domain_docs: int
    max_source_files_before_coding: int


CONTEXT_BUDGET: ContextBudget = {
    "task_file": 1,
    "global_rules": 1,
    "max_architecture_domain_docs": 3,
    "max_source_files_before_coding": 8,
}

# ---------------------------------------------------------------------------
# Change discipline rules
# ---------------------------------------------------------------------------

CHANGE_DISCIPLINE_RULES: tuple[str, ...] = (
    "No speculative refactor.",
    "No new dependency unless required by the task.",
    "No package swap without an ADR.",
    "No schema change without migration + rollback consideration.",
    "No permission change without negative authorization tests.",
    "No clinical result workflow change without audit/version tests.",
)

# ---------------------------------------------------------------------------
# Composite export
# ---------------------------------------------------------------------------

class AgentContextBaseline(TypedDict):
    version: int
    context_routes: tuple[ContextRoute, ...]
    context_compression_rules: tuple[str, ...]
    task_execution_steps: tuple[str, ...]
    context_budget: ContextBudget
    change_discipline_rules: tuple[str, ...]


AGENT_CONTEXT_BASELINE: AgentContextBaseline = {
    "version": 1,
    "context_routes": CONTEXT_ROUTES,
    "context_compression_rules": CONTEXT_COMPRESSION_RULES,
    "task_execution_steps": TASK_EXECUTION_STEPS,
    "context_budget": CONTEXT_BUDGET,
    "change_discipline_rules": CHANGE_DISCIPLINE_RULES,
}

"""Meta / contracts router.

Exposes the frozen design-time contracts (scope, architecture, glossary,
performance budget, UI/UX baseline, agent context) as read-only endpoints.
These are dev/ops reference endpoints — not customer-facing API surface.
"""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import APIRouter

_repo_root = str(Path(__file__).resolve().parents[5])
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from contracts.agent_context_baseline import AGENT_CONTEXT_BASELINE  # noqa: E402
from contracts.architecture import ARCHITECTURE  # noqa: E402
from contracts.domain_glossary import CANONICAL_ENTITIES, FORBIDDEN_SYNONYMS  # noqa: E402
from contracts.performance_budget import PERFORMANCE_BUDGET  # noqa: E402
from contracts.ui_ux_baseline import UI_UX_BASELINE  # noqa: E402

router = APIRouter(tags=["meta"])

_SCOPE_FREEZE: dict = {
    "status": "FROZEN",
    "freeze_date": "2026-10-08",
    "document_version": "1.0.0",
    "boundaries": {
        "mvp": {
            "phases": ["P00", "P01", "P02", "P03", "P04", "P05", "P06"],
            "modules": [
                "identity_rbac",
                "patient_management",
                "registration_orders",
                "pathology_lims",
                "billing_referral",
                "report_engine",
            ],
            "deployment_modes": ["cloud", "local_multi_pc"],
        },
        "v1": {
            "phases": ["P07", "P08", "P09"],
            "modules": ["blood_bank", "analyzer_integration", "hybrid_offline"],
            "deployment_modes": ["offline", "hybrid"],
        },
        "v2": {
            "phases": ["P10", "P11", "P12", "P13"],
            "modules": ["ux_polish", "desktop_mobile", "hardening", "launch"],
            "deployment_modes": [],
        },
    },
    "assumptions_count": 10,
    "open_decisions_count": 7,
}


@router.get("/scope-freeze", summary="Frozen scope boundaries")
def scope_freeze() -> dict:
    return _SCOPE_FREEZE


@router.get("/domain-glossary", summary="Canonical domain vocabulary")
def domain_glossary() -> dict:
    return {
        "entity_count": len(CANONICAL_ENTITIES),
        "entities": CANONICAL_ENTITIES,
        "forbidden_synonyms": FORBIDDEN_SYNONYMS,
    }


@router.get("/architecture", summary="Architecture baseline")
def architecture() -> dict:
    return ARCHITECTURE


@router.get("/ui-ux-baseline", summary="UI/UX baseline conventions")
def ui_ux_baseline() -> dict:
    return UI_UX_BASELINE


@router.get("/performance-budget", summary="Performance budgets")
def performance_budget() -> dict:
    return PERFORMANCE_BUDGET


@router.get("/agent-context-baseline", summary="Agent context baseline")
def agent_context_baseline() -> dict:
    return AGENT_CONTEXT_BASELINE

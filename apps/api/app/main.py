import sys
from pathlib import Path

from fastapi import FastAPI

# Allow importing from the contracts package at the repo root.
_repo_root = str(Path(__file__).resolve().parents[3])
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from contracts.domain_glossary import (  # noqa: E402
    CANONICAL_ENTITIES,
    FORBIDDEN_SYNONYMS,
)
from contracts.architecture import ARCHITECTURE  # noqa: E402

app = FastAPI(title="Aarozi Healthcare API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "api"}


SCOPE_FREEZE = {
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
            "modules": [
                "blood_bank",
                "analyzer_integration",
                "hybrid_offline",
            ],
            "deployment_modes": ["offline", "hybrid"],
        },
        "v2": {
            "phases": ["P10", "P11", "P12", "P13"],
            "modules": [
                "ux_polish",
                "desktop_mobile",
                "hardening",
                "launch",
            ],
            "deployment_modes": [],
        },
    },
    "assumptions_count": 10,
    "open_decisions_count": 7,
}


@app.get("/scope-freeze")
def scope_freeze() -> dict:
    """Return the frozen scope boundaries, assumptions count and open decisions count."""
    return SCOPE_FREEZE


@app.get("/domain-glossary")
def domain_glossary() -> dict:
    """Return the canonical domain vocabulary and forbidden synonyms."""
    return {
        "entity_count": len(CANONICAL_ENTITIES),
        "entities": CANONICAL_ENTITIES,
        "forbidden_synonyms": FORBIDDEN_SYNONYMS,
    }


@app.get("/architecture")
def architecture() -> dict:
    """Return the frozen architecture baseline."""
    return ARCHITECTURE


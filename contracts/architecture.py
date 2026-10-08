"""Frozen architecture baseline for Aarozi Healthcare.

This module encodes the modular-monolith boundaries, domain modules,
deployment modes, technology stack and request-path convention that
were locked during the P00-03 Architecture Baseline task.

Usage:
    from contracts.architecture import ARCHITECTURE
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Domain modules — logical boundaries inside the monolith.
# Each module owns its schema, services, and event contracts.
# ---------------------------------------------------------------------------

DOMAIN_MODULES: list[str] = [
    "platform",
    "identity_rbac",
    "patient",
    "pathology",
    "billing",
    "referral",
    "reporting",
    "blood_bank",
    "inventory",
    "integrations",
    "sync",
    "licensing",
    "notifications",
]

# ---------------------------------------------------------------------------
# Deployment modes supported by the product.
# ---------------------------------------------------------------------------

DEPLOYMENT_MODES: list[dict[str, str]] = [
    {
        "id": "cloud",
        "name": "Cloud SaaS",
        "description": "Multi-tenant SaaS, internet required.",
    },
    {
        "id": "local_multi_pc",
        "name": "Local Multi-PC",
        "description": "Local server as LAN source of truth; internet not required for core workflows.",
    },
    {
        "id": "offline",
        "name": "Offline / Local",
        "description": "Fully disconnected site; file-based license activation.",
    },
    {
        "id": "hybrid",
        "name": "Hybrid",
        "description": "Local-first with optional cloud sync.",
    },
]

# ---------------------------------------------------------------------------
# Technology stack
# ---------------------------------------------------------------------------

TECH_STACK: dict[str, str | list[str]] = {
    "api_framework": "FastAPI",
    "language": "Python 3.11+",
    "orm": "SQLAlchemy 2.x",
    "database": "PostgreSQL",
    "cache": "Redis",
    "migrations": "Alembic",
    "object_storage": "S3-compatible / local filesystem",
    "client_surfaces": [
        "Web (SPA)",
        "Tauri Desktop",
        "Flutter Mobile",
        "Local Analyzer Connector",
    ],
    "desktop_framework": "Tauri",
    "mobile_framework": "Flutter",
}

# ---------------------------------------------------------------------------
# Request path convention
# ---------------------------------------------------------------------------

REQUEST_PATH: list[str] = [
    "UI / Client",
    "Auth / Session",
    "Authorization (RBAC)",
    "Application Service",
    "Transaction",
    "Event / Outbox",
    "Background Worker",
]

# ---------------------------------------------------------------------------
# Architectural rules
# ---------------------------------------------------------------------------

ARCHITECTURE_RULES: list[str] = [
    "Modular monolith — no microservice extraction during MVP.",
    "Each domain module owns its schema, services, and event contracts.",
    "Local multi-PC uses a dedicated local server + PostgreSQL as LAN source of truth.",
    "Desktop clients do not keep independent primary databases.",
    "Offline licenses are signed documents verified locally with a public key.",
    "The application never contains a production private signing key.",
    "Cloud sync, cloud backup and remote access are optional entitlements.",
    "Offline product must not require cloud endpoints for core workflows.",
    "Upgrading to hybrid mode must not require reinstalling or recreating local data.",
    "No service extraction without an Architecture Decision Record (ADR).",
]

# ---------------------------------------------------------------------------
# Composite export
# ---------------------------------------------------------------------------

ARCHITECTURE: dict = {
    "style": "modular_monolith",
    "domain_modules": DOMAIN_MODULES,
    "domain_module_count": len(DOMAIN_MODULES),
    "deployment_modes": DEPLOYMENT_MODES,
    "deployment_mode_count": len(DEPLOYMENT_MODES),
    "tech_stack": TECH_STACK,
    "request_path": REQUEST_PATH,
    "rules": ARCHITECTURE_RULES,
    "rule_count": len(ARCHITECTURE_RULES),
}

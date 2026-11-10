from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure contracts package (repo root) is importable
_repo_root = str(Path(__file__).resolve().parents[3])
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from app.errors import register_exception_handlers  # noqa: E402
from app.middleware import RequestIDMiddleware  # noqa: E402
from app.routers import (  # noqa: E402
    auth,
    backup,
    billing,
    blood_bank,
    corporate,
    customer_portal,
    expenses,
    google_drive,
    health,
    home_collection,
    integrations,
    inventory,
    licensing,
    meta,
    migration,
    pathology,
    patients,
    payments,
    quality,
    radiology,
    reports,
    sync,
)
from app.settings import get_settings  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Open connections on startup; close them on shutdown."""
    from app.cache import get_redis  # noqa: F401
    from app.db import get_engine  # noqa: F401

    yield

    from app.cache import close_redis
    from app.db import close_db

    await close_redis()
    await close_db()


def create_app() -> FastAPI:
    settings = get_settings()

    application = FastAPI(
        title="Aarozi Healthcare API",
        version="0.1.0",
        description=(
            "Unified Diagnostic Laboratory + Blood Bank + Billing platform API. "
            "Supports cloud, local multi-PC, offline, and hybrid deployment modes."
        ),
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # Middleware (outermost registered last, executes first)
    application.add_middleware(RequestIDMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if not settings.is_production else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    register_exception_handlers(application)

    # Routers
    application.include_router(health.router)
    application.include_router(meta.router)
    application.include_router(auth.router)
    application.include_router(patients.router)
    application.include_router(pathology.router)
    application.include_router(billing.router)
    application.include_router(blood_bank.router)
    application.include_router(reports.router)
    application.include_router(integrations.router)
    application.include_router(sync.router)
    application.include_router(licensing.router)
    application.include_router(payments.router)
    application.include_router(customer_portal.router)
    application.include_router(backup.router)
    application.include_router(google_drive.router)
    application.include_router(migration.router)
    application.include_router(expenses.router)
    application.include_router(home_collection.router)
    application.include_router(inventory.router)
    application.include_router(radiology.router)
    application.include_router(corporate.router)
    application.include_router(quality.router)

    # Mount static frontend if available for offline/monolith distribution
    root_p = Path(__file__).resolve().parents[3]
    static_candidates = [
        root_p / "dist" / "public",
        root_p / "apps" / "web" / ".output" / "public",
        Path(__file__).resolve().parent / "static",
    ]
    for s_dir in static_candidates:
        if s_dir.exists() and (s_dir / "index.html").exists():
            from fastapi.staticfiles import StaticFiles
            application.mount("/", StaticFiles(directory=str(s_dir), html=True), name="static_frontend")
            break

    return application


app = create_app()
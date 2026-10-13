"""Health check router.

Provides shallow liveness and deep readiness endpoints.
Both are intentionally kept dependency-free from auth middleware
so infrastructure tooling (load balancers, k8s probes) can reach them.
"""

from __future__ import annotations

import sqlalchemy

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness probe")
def health() -> dict[str, str]:
    """Returns 200 immediately — confirms the process is alive."""
    return {"status": "ok", "service": "api"}


@router.get("/health/ready", summary="Readiness probe")
async def health_ready() -> dict[str, object]:
    """Deep readiness — pings PostgreSQL and Redis.

    Returns 200 in all cases; the *status* field indicates degraded state.
    This avoids cascading 503s when a backend is temporarily unavailable.
    """
    from app.cache import redis_ping
    from app.db import get_engine

    db_ok = False
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(sqlalchemy.text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    redis_ok = await redis_ping()

    overall = "ok" if (db_ok and redis_ok) else "degraded"
    return {
        "status": overall,
        "database": "ok" if db_ok else "unavailable",
        "redis": "ok" if redis_ok else "unavailable",
    }

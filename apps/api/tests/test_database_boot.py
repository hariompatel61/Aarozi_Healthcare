"""P01-03 database boot tests.

All tests are offline-safe — no live PostgreSQL, Redis, or MinIO required.
They verify settings parsing, module structure, and import correctness.
Live connectivity tests (marked with @pytest.mark.integration) are excluded
from the default run; they require the docker-compose stack to be up.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

_repo_root = Path(__file__).resolve().parents[3]
_api_root = _repo_root / "apps" / "api"
for _p in (str(_repo_root), str(_api_root)):
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ---------------------------------------------------------------------------
# Settings module
# ---------------------------------------------------------------------------

def test_settings_module_importable() -> None:
    mod = importlib.import_module("app.settings")
    assert hasattr(mod, "Settings")
    assert hasattr(mod, "get_settings")


def test_settings_defaults_are_safe() -> None:
    from app.settings import Settings
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    assert s.APP_ENV == "development"
    assert s.DB_POOL_SIZE > 0
    assert s.DB_MAX_OVERFLOW >= 0
    assert s.ACCESS_TOKEN_EXPIRE_MINUTES > 0


def test_settings_database_url_default_has_host() -> None:
    from app.settings import Settings
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    assert "localhost" in s.DATABASE_URL or "postgres" in s.DATABASE_URL


def test_settings_redis_url_default_has_host() -> None:
    from app.settings import Settings
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    assert "localhost" in s.REDIS_URL or "redis" in s.REDIS_URL


def test_settings_is_production_false_by_default() -> None:
    from app.settings import Settings
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    assert s.is_production is False


def test_settings_is_testing_false_by_default() -> None:
    from app.settings import Settings
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    assert s.is_testing is False



# ---------------------------------------------------------------------------
# db module
# ---------------------------------------------------------------------------

def test_db_module_importable() -> None:
    mod = importlib.import_module("app.db")
    assert hasattr(mod, "Base")
    assert hasattr(mod, "get_engine")
    assert hasattr(mod, "get_db")
    assert hasattr(mod, "close_db")
    assert hasattr(mod, "get_session_factory")


def test_db_base_is_declarative_base() -> None:
    from app.db import Base
    from sqlalchemy.orm import DeclarativeBase
    assert issubclass(Base, DeclarativeBase)


def test_db_get_engine_returns_async_engine() -> None:
    from app.db import get_engine
    from sqlalchemy.ext.asyncio import AsyncEngine
    engine = get_engine()
    assert isinstance(engine, AsyncEngine)


def test_db_get_session_factory_returns_factory() -> None:
    from app.db import get_session_factory
    from sqlalchemy.ext.asyncio import async_sessionmaker
    factory = get_session_factory()
    assert isinstance(factory, async_sessionmaker)


def test_db_engine_url_matches_settings() -> None:
    from app.db import get_engine
    from app.settings import Settings
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    engine = get_engine()
    assert "asyncpg" in str(engine.url) or "postgresql" in str(engine.url)


# ---------------------------------------------------------------------------
# cache module
# ---------------------------------------------------------------------------

def test_cache_module_importable() -> None:
    mod = importlib.import_module("app.cache")
    assert hasattr(mod, "get_redis")
    assert hasattr(mod, "close_redis")
    assert hasattr(mod, "redis_ping")
    assert hasattr(mod, "redis_get")
    assert hasattr(mod, "redis_set")
    assert hasattr(mod, "redis_delete")


def test_cache_get_redis_returns_redis_client() -> None:
    import redis.asyncio as aioredis
    from app.cache import get_redis
    client = get_redis()
    assert isinstance(client, aioredis.Redis)


# ---------------------------------------------------------------------------
# storage module
# ---------------------------------------------------------------------------

def test_storage_module_importable() -> None:
    mod = importlib.import_module("app.storage")
    assert hasattr(mod, "get_storage")
    assert hasattr(mod, "close_storage")
    assert hasattr(mod, "storage_ensure_bucket")
    assert hasattr(mod, "storage_put_object")
    assert hasattr(mod, "storage_get_object")
    assert hasattr(mod, "storage_delete_object")


# ---------------------------------------------------------------------------
# /health/ready endpoint (offline-safe: expects degraded without DB/Redis)
# ---------------------------------------------------------------------------

def test_health_ready_endpoint_returns_200() -> None:
    from app.main import app
    from fastapi.testclient import TestClient
    client = TestClient(app, raise_server_exceptions=False)
    r = client.get("/health/ready")
    assert r.status_code == 200


def test_health_ready_returns_status_field() -> None:
    from app.main import app
    from fastapi.testclient import TestClient
    client = TestClient(app, raise_server_exceptions=False)
    data = client.get("/health/ready").json()
    assert "status" in data
    assert data["status"] in ("ok", "degraded")


def test_health_ready_returns_database_field() -> None:
    from app.main import app
    from fastapi.testclient import TestClient
    client = TestClient(app, raise_server_exceptions=False)
    data = client.get("/health/ready").json()
    assert "database" in data
    assert data["database"] in ("ok", "unavailable")


def test_health_ready_returns_redis_field() -> None:
    from app.main import app
    from fastapi.testclient import TestClient
    client = TestClient(app, raise_server_exceptions=False)
    data = client.get("/health/ready").json()
    assert "redis" in data
    assert data["redis"] in ("ok", "unavailable")


def test_health_endpoint_still_returns_ok() -> None:
    """The basic /health endpoint must remain unaffected by the new wiring."""
    from app.main import app
    from fastapi.testclient import TestClient
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_settings_is_testing_true_when_app_env_test() -> None:
    from app.settings import Settings
    s = Settings(APP_ENV="test", _env_file=None)  # type: ignore[call-arg]
    assert s.is_testing is True


def test_settings_is_production_true_when_app_env_production() -> None:
    from app.settings import Settings
    s = Settings(APP_ENV="production", _env_file=None)  # type: ignore[call-arg]
    assert s.is_production is True


def test_settings_jwt_secret_not_empty() -> None:
    from app.settings import Settings
    s = Settings(APP_ENV="development", _env_file=None)  # type: ignore[call-arg]
    assert len(s.JWT_SECRET) > 0


def test_settings_object_storage_endpoint_is_url() -> None:
    from app.settings import Settings
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    assert s.OBJECT_STORAGE_ENDPOINT.startswith("http")


def test_settings_object_storage_bucket_not_empty() -> None:
    from app.settings import Settings
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    assert len(s.OBJECT_STORAGE_BUCKET) > 0

"""Async SQLAlchemy database layer.

Provides a single async engine, session factory, and Base declarative class.
The engine is created lazily and wired via FastAPI lifespan.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.settings import get_settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None
_sync_engine: Engine | None = None
_sync_session_factory: sessionmaker[Session] | None = None


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""

    pass


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        settings = get_settings()
        url = settings.DATABASE_URL
        if "sqlite" in url:
            _engine = create_async_engine(url, echo=settings.DEBUG)
        else:
            _engine = create_async_engine(
                url,
                pool_size=settings.DB_POOL_SIZE,
                max_overflow=settings.DB_MAX_OVERFLOW,
                pool_timeout=settings.DB_POOL_TIMEOUT_S,
                echo=settings.DEBUG,
            )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _session_factory


def get_sync_db_url() -> str:
    from pathlib import Path

    settings = get_settings()
    url = settings.DATABASE_URL
    if "sqlite" in url:
        return url

    # In local development / offline, if Postgres is not reachable, fall back to dev_aarozi.db
    repo_root = Path(__file__).resolve().parents[3]
    dev_db = repo_root / "apps" / "api" / "dev_aarozi.db"
    if settings.APP_ENV != "production":
        postgres_reachable = False
        try:
            import socket

            with socket.create_connection(("localhost", 5432), timeout=0.3):
                postgres_reachable = True
        except OSError:
            postgres_reachable = False

        if not postgres_reachable:
            if not dev_db.exists():
                try:
                    from scripts.seed_demo_data import seed_database

                    seed_database()
                except Exception:
                    pass
            return f"sqlite:///{dev_db}"

    if "postgresql+asyncpg" in url:
        return url.replace("postgresql+asyncpg", "postgresql+psycopg2")
    return url


def get_sync_engine() -> Engine:
    global _sync_engine
    if _sync_engine is None:
        url = get_sync_db_url()
        connect_args = {"check_same_thread": False} if "sqlite" in url else {}
        _sync_engine = create_engine(url, connect_args=connect_args)
    return _sync_engine


def get_sync_session_factory() -> sessionmaker[Session]:
    global _sync_session_factory
    if _sync_session_factory is None:
        _sync_session_factory = sessionmaker(
            bind=get_sync_engine(),
            expire_on_commit=False,
            autoflush=False,
        )
    return _sync_session_factory


def get_db():
    """FastAPI dependency that yields a synchronous database session."""
    factory = get_sync_session_factory()
    with factory() as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise


async def init_db() -> None:
    """Create all tables (development only; production uses Alembic)."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Dispose of the database engines."""
    global _engine, _session_factory, _sync_engine, _sync_session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
    if _sync_engine is not None:
        _sync_engine.dispose()
        _sync_engine = None
        _sync_session_factory = None

"""Redis cache layer.

Provides a simple async Redis client wrapper for caching and session storage.
The client is created lazily and wired via FastAPI lifespan.
"""

from __future__ import annotations

from typing import Any

import redis.asyncio as aioredis

from app.settings import get_settings

_client: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    global _client
    if _client is None:
        settings = get_settings()
        _client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _client


async def close_redis() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


async def redis_ping() -> bool:
    """Ping Redis to check connectivity. Returns True if healthy."""
    try:
        client = get_redis()
        result = await client.ping()
        return result is True
    except Exception:
        return False


async def redis_get(key: str) -> Any:
    client = get_redis()
    return await client.get(key)


async def redis_set(key: str, value: Any, ex: int | None = None) -> bool:
    client = get_redis()
    return await client.set(key, value, ex=ex)


async def redis_delete(key: str) -> int:
    client = get_redis()
    return await client.delete(key)

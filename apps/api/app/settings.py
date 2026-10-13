
"""Application configuration via pydantic-settings.

Reads from environment variables and falls back to safe local defaults.
Does not log secrets.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Runtime environment
    APP_ENV: Literal["development", "test", "staging", "production"] = "development"
    DEBUG: bool = False

    # Server binding
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # PostgreSQL
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://aarozi:aarozi@localhost:5432/aarozi_healthcare",
        description="Async PostgreSQL connection string",
    )
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT_S: float = 30.0

    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection string",
    )

    # MinIO / S3 Object Storage
    OBJECT_STORAGE_ENDPOINT: str = "http://localhost:9000"
    OBJECT_STORAGE_BUCKET: str = "aarozi-dev"
    OBJECT_STORAGE_ACCESS_KEY: str = "aarozi"
    OBJECT_STORAGE_SECRET_KEY: str = "aarozi-development-only"
    OBJECT_STORAGE_SECURE: bool = False

    # Auth
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_testing(self) -> bool:
        return self.APP_ENV == "test"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

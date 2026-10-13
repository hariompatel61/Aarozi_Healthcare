"""Object storage layer (MinIO/S3).

Provides a simple async wrapper for object storage operations.
The client is created lazily and wired via FastAPI lifespan.
"""

from __future__ import annotations

from io import BytesIO
from typing import Any

from app.settings import get_settings

# MinIO client is synchronous; we wrap it for the API.
# For production async needs, consider aiobotocore or minio-async.
try:
    from minio import Minio
    from minio.error import S3Error

    HAS_MINIO = True
except ImportError:
    Minio = None  # type: ignore[misc, assignment]
    S3Error = Exception  # type: ignore[misc, assignment]
    HAS_MINIO = False

_client: Minio | None = None


def get_storage() -> Minio:
    global _client
    if _client is None:
        if not HAS_MINIO:
            raise RuntimeError("minio package not installed")
        settings = get_settings()
        _client = Minio(
            settings.OBJECT_STORAGE_ENDPOINT.replace("http://", "").replace(
                "https://", ""
            ),
            access_key=settings.OBJECT_STORAGE_ACCESS_KEY,
            secret_key=settings.OBJECT_STORAGE_SECRET_KEY,
            secure=settings.OBJECT_STORAGE_SECURE,
        )
    return _client


async def close_storage() -> None:
    global _client
    _client = None


async def storage_ensure_bucket() -> bool:
    """Ensure the configured bucket exists. Returns True if healthy."""
    try:
        client = get_storage()
        settings = get_settings()
        if not client.bucket_exists(settings.OBJECT_STORAGE_BUCKET):
            client.make_bucket(settings.OBJECT_STORAGE_BUCKET)
        return True
    except Exception:
        return False


async def storage_put_object(
    object_name: str,
    data: bytes,
    metadata: dict[str, str] | None = None,
) -> str:
    client = get_storage()
    settings = get_settings()
    client.put_object(
        settings.OBJECT_STORAGE_BUCKET,
        object_name,
        BytesIO(data),
        length=len(data),
        metadata=metadata,
    )
    return object_name


async def storage_get_object(object_name: str) -> bytes:
    client = get_storage()
    settings = get_settings()
    response = client.get_object(settings.OBJECT_STORAGE_BUCKET, object_name)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


async def storage_delete_object(object_name: str) -> bool:
    client = get_storage()
    settings = get_settings()
    client.remove_object(settings.OBJECT_STORAGE_BUCKET, object_name)
    return True

"""Shared Pydantic response schemas.

All API responses use these envelopes for consistency.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Structured error payload returned in all error responses."""

    code: str = Field(description="Machine-readable error code, e.g. 'not_found'")
    message: str = Field(description="Human-readable description")
    field: str | None = Field(default=None, description="Field name for validation errors")


class APIResponse(BaseModel, Generic[T]):
    """Standard success envelope wrapping any payload."""

    ok: bool = True
    data: T


class ErrorResponse(BaseModel):
    """Standard error envelope."""

    ok: bool = False
    error: ErrorDetail


class PaginatedResponse(BaseModel, Generic[T]):
    """Cursor-paginated list envelope.

    Uses cursor-based pagination (no OFFSET) to avoid unbounded queries.
    """

    ok: bool = True
    data: list[T]
    total: int | None = Field(
        default=None,
        description="Total record count (omit when expensive to compute)",
    )
    next_cursor: str | None = Field(
        default=None,
        description="Opaque cursor for the next page; null when no more pages",
    )
    page_size: int

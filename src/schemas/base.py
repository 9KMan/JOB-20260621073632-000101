// src/schemas/base.py
"""Base schemas shared across the application."""
from datetime import datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        ser_json_timedelta="iso8601",
        ser_json_bytes="base64",
    )


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""

    created_at: datetime
    updated_at: datetime


class UUIDMixin(BaseModel):
    """Mixin for UUID id field."""

    id: UUID


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""

    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str
    code: str | None = None
    field: str | None = None


class SuccessResponse(BaseModel):
    """Standard success response."""

    message: str
    data: dict | None = None

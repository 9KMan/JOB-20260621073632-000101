// src/app/schemas/base.py
"""Base schemas for API responses."""
from datetime import datetime
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )


class TimestampSchema(BaseSchema):
    """Schema with timestamp fields."""

    created_at: datetime
    updated_at: datetime


class UUIDSchema(TimestampSchema):
    """Schema with UUID primary key."""

    id: UUID


class PaginationParams(BaseModel):
    """Pagination parameters."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


T = TypeVar("T")


class PaginatedResponse(BaseSchema, Generic[T]):
    """Paginated response wrapper."""

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class SuccessResponse(BaseSchema):
    """Generic success response."""

    success: bool = True
    message: str
    data: dict[str, Any] | None = None


class ErrorDetail(BaseSchema):
    """Error detail schema."""

    loc: list[str] | None = None
    msg: str
    type: str


class ErrorResponse(BaseSchema):
    """Error response schema."""

    success: bool = False
    error: str
    detail: list[ErrorDetail] | None = None
    status_code: int

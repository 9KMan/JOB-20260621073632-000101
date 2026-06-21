// src/app/schemas/base.py
"""
Base Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
    )


class TimestampSchema(BaseSchema):
    """Schema with timestamp fields."""
    created_at: datetime
    updated_at: datetime


class UUIDSchema(BaseSchema):
    """Schema with UUID field."""
    id: UUID


class SoftDeleteSchema(BaseSchema):
    """Schema with soft delete fields."""
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None


class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""
    items: list[T]
    total: int
    page: int
    per_page: int
    pages: int


class ErrorResponse(BaseSchema):
    """Error response schema."""
    detail: str
    error_code: Optional[str] = None


class SuccessResponse(BaseSchema):
    """Success response schema."""
    message: str
    data: Optional[dict] = None

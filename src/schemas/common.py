// src/schemas/common.py
"""Common Pydantic schemas."""
from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    model_config = ConfigDict(from_attributes=True)


class TimestampMixin(BaseSchema):
    """Schema for timestamp fields."""
    created_at: datetime
    updated_at: datetime


class SoftDeleteMixin(BaseSchema):
    """Schema for soft delete fields."""
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None


class PaginatedResponse(BaseSchema, Generic[T]):
    """Paginated response wrapper."""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class ErrorResponse(BaseSchema):
    """Standard error response."""
    error: str
    message: str
    details: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuccessResponse(BaseSchema):
    """Standard success response."""
    success: bool = True
    message: str
    data: Optional[dict] = None


class HealthCheckResponse(BaseSchema):
    """Health check response."""
    status: str
    version: str
    database: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginationParams(BaseSchema):
    """Pagination parameters."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

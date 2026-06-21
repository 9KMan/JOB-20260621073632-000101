// src/app/schemas/common.py
"""
Common Pydantic schemas.
"""
from typing import Generic, TypeVar, Optional, List, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

T = TypeVar("T")


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    total: int
    page: int
    per_page: int
    total_pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    items: List[T]
    meta: PaginationMeta


class SearchParams(BaseModel):
    """Common search parameters."""
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)
    sort_by: Optional[str] = Field(default=None)
    sort_order: str = Field(default="asc", pattern="^(asc|desc)$")


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Error response."""
    detail: str
    errors: Optional[List[Dict[str, Any]]] = None


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""
    created_at: datetime
    updated_at: datetime


class AuditMixin(BaseModel):
    """Mixin for audit fields."""
    created_by: Optional[str] = None
    updated_by: Optional[str] = None


class BaseSchema(BaseModel):
    """Base schema with configuration."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        validate_assignment=True,
    )


class UUIDMixin(BaseModel):
    """Mixin for UUID id field."""
    id: str

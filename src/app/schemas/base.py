# src/app/schemas/base.py
"""Base schemas for common fields."""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        validate_assignment=True,
    )


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""
    
    created_at: datetime
    updated_at: datetime


class UUIDMixin(BaseModel):
    """Mixin for UUID id field."""
    
    id: uuid.UUID


class SoftDeleteMixin(BaseModel):
    """Mixin for soft delete fields."""
    
    deleted_at: Optional[datetime] = None


class PaginationParams(BaseModel):
    """Pagination parameters."""
    
    page: int = 1
    page_size: int = 20
    max_page_size: int = 100


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    
    items: list
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool

# src/schemas/common.py
from typing import TypeVar, Generic, List, Optional, Any
from datetime import datetime

from pydantic import BaseModel, Field


T = TypeVar("T")


class PageParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    @classmethod
    def create(cls, items: List[T], total: int, params: PageParams):
        total_pages = (total + params.page_size - 1) // params.page_size
        return cls(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages
        )


class TimestampMixinSchema(BaseModel):
    """Schema mixin for timestamps."""
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class UUIDMixinSchema(BaseModel):
    """Schema mixin for UUID."""
    id: str
    
    model_config = {"from_attributes": True}

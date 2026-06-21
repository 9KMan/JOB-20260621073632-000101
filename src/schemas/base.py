// src/schemas/base.py
"""Base Pydantic schemas."""
from typing import Generic, TypeVar, List, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict


T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        validate_assignment=True
    )


class TimestampSchema(BaseSchema):
    """Schema with timestamp fields."""
    
    created_at: datetime
    updated_at: datetime


class UUIDSchema(BaseSchema):
    """Schema with UUID identifier."""
    
    id: UUID


class TimestampUUIDSchema(TimestampSchema, UUIDSchema):
    """Schema with both timestamps and UUID."""
    pass


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""
    
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    
    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        page_size: int
    ) -> "PaginatedResponse[T]":
        """Create a paginated response."""
        total_pages = (total + page_size - 1) // page_size
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )

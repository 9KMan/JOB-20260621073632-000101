// src/schemas/base.py
"""Base Pydantic schemas."""
from typing import Generic, TypeVar, Optional, List, Any
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


T = TypeVar("T")


class BaseResponse(BaseModel):
    """Base response schema."""
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class PaginationParams(BaseModel):
    """Pagination parameters."""
    
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        page_size: int
    ) -> "PaginatedResponse[T]":
        """Create a paginated response."""
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )


class ErrorResponse(BaseModel):
    """Error response schema."""
    
    detail: str
    code: Optional[str] = None
    errors: Optional[List[dict]] = None


class SuccessResponse(BaseModel):
    """Generic success response."""
    
    success: bool = True
    message: str
    data: Optional[Any] = None

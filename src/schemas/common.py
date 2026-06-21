# src/schemas/common.py
"""Common Pydantic schemas."""
from typing import Generic, TypeVar, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    
    total: int = Field(..., description="Total number of records")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of records per page")
    total_pages: int = Field(..., description="Total number of pages")
    items: List[T] = Field(..., description="List of items in current page")
    
    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    """Simple message response."""
    
    message: str = Field(..., description="Response message")
    success: bool = Field(default=True, description="Success status")


class ErrorResponse(BaseModel):
    """Error response schema."""
    
    detail: str = Field(..., description="Error detail message")
    error_code: Optional[str] = Field(None, description="Error code")
    field_errors: Optional[List[dict]] = Field(None, description="Field-specific errors")


class PaginationParams(BaseModel):
    """Pagination parameters."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Page size")
    search: Optional[str] = Field(None, description="Search query")
    sort_by: Optional[str] = Field(None, description="Sort field")
    sort_order: Optional[str] = Field("asc", pattern="^(asc|desc)$", description="Sort order")


class UUIDMixin(BaseModel):
    """Mixin for UUID id field."""
    
    id: UUID


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""
    
    created_at: str
    updated_at: str

// src/app/schemas/common.py
"""Common Pydantic schemas."""
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field, ConfigDict


T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        """Calculate offset."""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Get limit."""
        return self.page_size


class ResponseMeta(BaseModel):
    """Response metadata."""
    
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0


class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""
    
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    meta: Optional[ResponseMeta] = None
    
    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    
    success: bool = True
    data: list[T] = []
    message: Optional[str] = None
    meta: ResponseMeta
    
    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    """Error response schema."""
    
    success: bool = False
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str = "healthy"
    version: str
    environment: str
    database: str = "connected"

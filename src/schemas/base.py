// src/schemas/base.py
"""
FinaRo AP Automation Core Engine
Base Pydantic Schemas
"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


T = TypeVar('T')


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
        arbitrary_types_allowed=True,
    )


class BaseResponse(BaseSchema, Generic[T]):
    """Standard API response wrapper."""
    success: bool = True
    message: Optional[str] = None
    data: Optional[T] = None
    errors: Optional[List[dict]] = None


class PaginatedResponse(BaseSchema, Generic[T]):
    """Paginated response wrapper."""
    success: bool = True
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[T]
    has_next: bool
    has_previous: bool


class ErrorResponse(BaseSchema):
    """Error response schema."""
    success: bool = False
    error_code: str
    message: str
    details: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginationParams(BaseSchema):
    """Pagination parameters."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: Optional[str] = None
    sort_order: str = Field(default="asc", pattern="^(asc|desc)$")
    
    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Get limit for database query."""
        return self.page_size


class FilterParams(BaseSchema):
    """Filter parameters for list endpoints."""
    supplier_id: Optional[UUID] = None
    status: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search: Optional[str] = None
    company_id: Optional[UUID] = None
    department: Optional[str] = None

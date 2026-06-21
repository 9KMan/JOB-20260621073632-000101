// src/schemas/common.py
"""Common Pydantic schemas."""
from typing import Any, Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field


ModelType = TypeVar("ModelType", bound=BaseModel)


class PaginationParams(BaseModel):
    """Pagination parameters."""

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @computed_field
    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.page_size

    @computed_field
    @property
    def limit(self) -> int:
        """Return page size as limit."""
        return self.page_size


class PaginatedResponse(BaseModel, Generic[ModelType]):
    """Paginated response wrapper."""

    model_config = ConfigDict(from_attributes=True)

    items: List[ModelType]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(
        cls,
        items: List[ModelType],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[ModelType]":
        """Create a paginated response."""
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Error response schema."""

    detail: str
    code: Optional[str] = None
    errors: Optional[List[dict[str, Any]]] = None


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        validate_assignment=True,
    )

# api/schemas/common.py
"""Common schemas for API responses."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field, field_validator

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: str | None = Field(default=None)
    sort_order: str = Field(default="asc", pattern="^(asc|desc)$")

    @field_validator("page")
    @classmethod
    def validate_page(cls, v: int) -> int:
        """Validate page number."""
        return max(1, v)

    @field_validator("page_size")
    @classmethod
    def validate_page_size(cls, v: int) -> int:
        """Validate page size."""
        return min(max(1, v), 100)


class Meta(BaseModel):
    """Pagination metadata."""

    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""

    items: list[T]
    meta: Meta


class ErrorDetail(BaseModel):
    """Error detail."""

    code: str
    message: str
    field: str | None = None


class ErrorResponse(BaseModel):
    """Error response."""

    error: str
    detail: list[ErrorDetail] | None = None
    request_id: str | None = None


class SuccessResponse(BaseModel):
    """Generic success response."""

    success: bool = True
    message: str
    data: dict[str, Any] | None = None

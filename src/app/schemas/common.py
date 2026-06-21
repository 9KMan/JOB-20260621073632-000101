// src/app/schemas/common.py
"""Common Pydantic schemas and utilities."""
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Generic type for paginated responses
T = TypeVar("T")


class UUIDMixin(BaseModel):
    """Schema mixin for UUID fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID


class TimestampMixin(BaseModel):
    """Schema mixin for timestamp fields."""

    created_at: datetime
    updated_at: datetime


class SoftDeleteMixin(BaseModel):
    """Schema mixin for soft delete fields."""

    is_deleted: bool = False
    deleted_at: datetime | None = None


class BaseSchema(UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Base schema combining common mixins."""

    pass


class PaginationParams(BaseModel):
    """Pagination parameters."""

    skip: int = Field(default=0, ge=0, description="Number of records to skip")
    limit: int = Field(default=100, ge=1, le=1000, description="Max records to return")
    order_by: str | None = Field(default=None, description="Field to order by")
    order_dir: str = Field(default="desc", pattern="^(asc|desc)$", description="Sort direction")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""

    items: list[T]
    total: int
    skip: int
    limit: int
    has_more: bool


class ErrorDetail(BaseModel):
    """Error detail schema."""

    field: str | None = None
    message: str
    code: str | None = None


class ErrorResponse(BaseModel):
    """Error response schema."""

    detail: str | list[ErrorDetail]
    error_code: str | None = None


class SuccessResponse(BaseModel):
    """Generic success response."""

    message: str
    data: dict | None = None


class DecimalField(BaseModel):
    """Schema for decimal fields."""

    value: Decimal = Field(ge=0)
    
    @field_validator("value", mode="before")
    @classmethod
    def validate_decimal(cls, v: Any) -> Decimal:
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        if isinstance(v, Decimal):
            return v
        raise ValueError("Invalid decimal value")


class DateField(BaseModel):
    """Schema for date fields."""

    value: date

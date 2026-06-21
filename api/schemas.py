// api/schemas.py
"""
Shared Pydantic request/response schemas.

These schemas are used across multiple API endpoints for common
request validation and response formatting.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator


T = TypeVar("T")


class HealthCheck(BaseModel):
    """Health check response schema."""

    status: str = Field(default="healthy")
    version: str = Field(default="0.1.0")
    database: str = Field(default="connected")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    error: str = Field(..., description="Error type/code")
    message: str = Field(..., description="Human-readable error message")
    details: dict[str, Any] | None = Field(
        default=None,
        description="Additional error details"
    )
    request_id: str | None = Field(
        default=None,
        description="Request ID for tracing"
    )


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: list[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @field_validator("page")
    @classmethod
    def validate_page(cls, v: int) -> int:
        if v < 1:
            return 1
        return v

    @field_validator("page_size")
    @classmethod
    def validate_page_size(cls, v: int) -> int:
        if v < 1:
            return 20
        if v > 100:
            return 100
        return v


class DateRangeParams(BaseModel):
    """Date range filter parameters."""

    start_date: date | None = Field(default=None)
    end_date: date | None = Field(default=None)

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v: date | None, info) -> date | None:
        start = info.data.get("start_date")
        if v and start and v < start:
            raise ValueError("end_date must be after start_date")
        return v


class MoneyAmount(BaseModel):
    """Monetary amount with currency."""

    model_config = ConfigDict(decimal_precision=2)

    amount: Decimal = Field(..., description="Monetary amount")
    currency: str = Field(default="USD", description="ISO 4217 currency code")


class Quantity(BaseModel):
    """Quantity with unit of measure."""

    model_config = ConfigDict(decimal_precision=4)

    quantity: Decimal = Field(..., description="Numeric quantity")
    unit: str = Field(default="EA", description="Unit of measure code")


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""

    created_at: datetime
    updated_at: datetime


class UUIDMixin(BaseModel):
    """Mixin for UUID id field."""

    id: uuid.UUID

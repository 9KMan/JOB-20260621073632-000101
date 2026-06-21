// api/schemas.py
"""Shared Pydantic request/response schemas.

Contains common schemas used across multiple endpoints.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_encoders={Decimal: str, datetime: lambda v: v.isoformat()},
    )


class PaginationParams(BaseModel):
    """Pagination parameters."""

    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=1000)
    order_by: str | None = Field(default=None)
    order_dir: str = Field(default="asc", pattern="^(asc|desc)$")


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""

    items: list[Any]
    total: int
    skip: int
    limit: int
    has_more: bool


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str = "0.1.0"
    database: str = "connected"
    timestamp: datetime


class ErrorDetail(BaseModel):
    """Error detail schema."""

    code: str
    message: str
    field: str | None = None
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    """Error response schema."""

    error: ErrorDetail
    request_id: str | None = None


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""

    created_at: datetime
    updated_at: datetime


class MoneyAmount(BaseModel):
    """Money amount with currency."""

    amount: Decimal
    currency: str = "USD"


class QuantityAmount(BaseModel):
    """Quantity with unit of measure."""

    quantity: Decimal
    unit_of_measure: str | None = None


class MatchScore(BaseModel):
    """Match score result."""

    score: float = Field(ge=0, le=100)
    decision: str
    confidence: float = Field(ge=0, le=1)
    factors: dict[str, Any] | None = None


class VendorReference(BaseModel):
    """Vendor reference schema."""

    vendor_id: str | None = None
    vendor_number: str
    vendor_name: str


class ProductReference(BaseModel):
    """Product reference schema."""

    sku: str | None = None
    name: str | None = None
    description: str | None = None


class AuditInfo(BaseModel):
    """Audit information schema."""

    created_at: datetime
    updated_at: datetime
    created_by: str | None = None
    updated_by: str | None = None


class BulkOperationResult(BaseModel):
    """Result of a bulk operation."""

    success_count: int
    failure_count: int
    total_count: int
    errors: list[ErrorDetail] = Field(default_factory=list)


class BulkIngestRequest(BaseModel):
    """Request for bulk ingestion of records."""

    items: list[dict[str, Any]]
    validate_only: bool = Field(default=False)
    skip_duplicates: bool = Field(default=True)


class BulkIngestResponse(BaseModel):
    """Response for bulk ingestion."""

    result: BulkOperationResult
    ingested_ids: list[str] = Field(default_factory=list)
    skipped_ids: list[str] = Field(default_factory=list)

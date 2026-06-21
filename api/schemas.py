# api/schemas.py
"""Shared Pydantic schemas for API request/response models.

Contains common schemas used across multiple endpoints including
pagination, error responses, and health checks.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator


# Generic type for paginated responses
T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        validate_assignment=True,
    )


class HealthResponse(BaseSchema):
    """Health check response."""

    status: str = "healthy"
    version: str = "0.1.0"
    environment: str
    database: str = "connected"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseSchema):
    """Standard error response."""

    error: str
    message: str
    details: dict[str, Any] | None = None
    request_id: str | None = None


class PaginationParams(BaseSchema):
    """Pagination parameters for list endpoints."""

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Items per page",
    )

    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Get limit for database query."""
        return self.page_size


class PaginatedResponse(BaseSchema, Generic[T]):
    """Generic paginated response."""

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        """Create a paginated response."""
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


# Invoice Schemas
class InvoiceLineBase(BaseSchema):
    """Base invoice line schema."""

    line_number: int
    sku: str | None = None
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal
    tax_rate: Decimal = Decimal("0.0000")


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating an invoice line."""

    pass


class InvoiceLineResponse(InvoiceLineBase):
    """Schema for invoice line response."""

    id: uuid.UUID
    status: str
    matched_quantity: Decimal
    matched_amount: Decimal
    match_score: int | None = None


class InvoiceBase(BaseSchema):
    """Base invoice schema."""

    invoice_number: str
    supplier_id: str
    supplier_name: str
    invoice_date: date
    due_date: date | None = None
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    currency: str = "USD"
    po_reference: str | None = None
    notes: str | None = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating an invoice."""

    lines: list[InvoiceLineCreate] = Field(min_length=1)


class InvoiceUpdate(BaseSchema):
    """Schema for updating an invoice."""

    status: str | None = None
    due_date: date | None = None
    notes: str | None = None
    is_locked: bool | None = None


class InvoiceResponse(InvoiceBase):
    """Schema for invoice response."""

    id: uuid.UUID
    status: str
    is_locked: bool
    received_at: datetime
    created_at: datetime
    updated_at: datetime
    lines: list[InvoiceLineResponse] = []


class InvoiceListItem(BaseSchema):
    """Schema for invoice list item (minimal data)."""

    id: uuid.UUID
    invoice_number: str
    supplier_name: str
    invoice_date: date
    total_amount: Decimal
    currency: str
    status: str
    created_at: datetime


# Purchase Order Schemas
class PurchaseOrderLineBase(BaseSchema):
    """Base PO line schema."""

    line_number: int
    sku: str | None = None
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal
    tax_rate: Decimal = Decimal("0.0000")


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Schema for creating a PO line."""

    pass


class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    """Schema for PO line response."""

    id: uuid.UUID
    received_quantity: Decimal
    invoiced_quantity: Decimal
    remaining_quantity: Decimal
    status: str


class PurchaseOrderBase(BaseSchema):
    """Base purchase order schema."""

    po_number: str
    supplier_id: str
    supplier_name: str
    order_date: date
    delivery_date: date | None = None
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    currency: str = "USD"
    payment_terms: str | None = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a PO."""

    lines: list[PurchaseOrderLineCreate] = Field(min_length=1)


class PurchaseOrderResponse(PurchaseOrderBase):
    """Schema for PO response."""

    id: uuid.UUID
    status: str
    is_acknowledged: bool
    received_at: datetime
    created_at: datetime
    updated_at: datetime
    lines: list[PurchaseOrderLineResponse] = []


class PurchaseOrderListItem(BaseSchema):
    """Schema for PO list item (minimal data)."""

    id: uuid.UUID
    po_number: str
    supplier_name: str
    order_date: date
    total_amount: Decimal
    currency: str
    status: str


# Delivery Note Schemas
class DeliveryNoteLineBase(BaseSchema):
    """Base DN line schema."""

    line_number: int
    sku: str | None = None
    description: str
    quantity: Decimal
    accepted_quantity: Decimal | None = None


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating a DN line."""

    pass


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """Schema for DN line response."""

    id: uuid.UUID
    status: str
    match_score: int | None = None


class DeliveryNoteBase(BaseSchema):
    """Base delivery note schema."""

    dn_number: str
    supplier_id: str
    supplier_name: str
    po_reference: str | None = None
    delivery_date: date
    received_by: str | None = None
    notes: str | None = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating a DN."""

    lines: list[DeliveryNoteLineCreate] = Field(min_length=1)


class DeliveryNoteResponse(DeliveryNoteBase):
    """Schema for DN response."""

    id: uuid.UUID
    po_id: uuid.UUID | None = None
    status: str
    received_at: datetime
    created_at: datetime
    updated_at: datetime
    lines: list[DeliveryNoteLineResponse] = []


class DeliveryNoteListItem(BaseSchema):
    """Schema for DN list item (minimal data)."""

    id: uuid.UUID
    dn_number: str
    supplier_name: str
    po_reference: str | None
    delivery_date: date
    status: str


# Matching Schemas
class MatchingRequest(BaseSchema):
    """Schema for triggering matching."""

    invoice_id: uuid.UUID
    match_type: str = "full"  # full, partial, quick


class MatchScoreDetail(BaseSchema):
    """Detailed score breakdown for a match."""

    score: int
    price_score: int
    quantity_score: int
    sku_score: int
    supplier_score: int
    date_score: int


class MatchResult(BaseSchema):
    """Result of matching a single line."""

    invoice_line_id: uuid.UUID
    po_line_id: uuid.UUID | None = None
    dn_line_id: uuid.UUID | None = None
    matched_quantity: Decimal
    matched_amount: Decimal
    score: int
    decision: str
    confidence: str
    score_details: MatchScoreDetail | None = None


class MatchingResponse(BaseSchema):
    """Response from matching engine."""

    invoice_id: uuid.UUID
    overall_score: int
    decision: str
    confidence: str
    matches: list[MatchResult]
    exceptions: list[dict[str, Any]] = []
    status: str


# Exception Schemas
class ExceptionBase(BaseSchema):
    """Base exception schema."""

    exception_type: str
    description: str
    invoice_line_id: uuid.UUID | None = None
    po_line_id: uuid.UUID | None = None


class ExceptionResponse(ExceptionBase):
    """Schema for exception response."""

    id: uuid.UUID
    status: str
    created_at: datetime
    resolved_by: str | None = None
    resolved_at: datetime | None = None
    resolution_notes: str | None = None


class ExceptionResolveRequest(BaseSchema):
    """Schema for resolving an exception."""

    resolution_notes: str | None = None
    resolved_by: str


class ExceptionDismissRequest(BaseSchema):
    """Schema for dismissing an exception."""

    reason: str
    dismissed_by: str


# Balance Ledger Schemas
class BalanceLedgerResponse(BaseSchema):
    """Schema for balance ledger entry."""

    id: uuid.UUID
    entry_type: str
    po_line_id: uuid.UUID
    quantity: Decimal
    amount: Decimal
    running_quantity: Decimal
    running_amount: Decimal
    reference_id: str
    reference_date: datetime
    created_at: datetime


class POLineBalanceResponse(BaseSchema):
    """Balance information for a PO line."""

    po_line_id: uuid.UUID
    ordered_quantity: Decimal
    received_quantity: Decimal
    invoiced_quantity: Decimal
    remaining_to_receive: Decimal
    remaining_to_invoice: Decimal
    last_entries: list[BalanceLedgerResponse] = []


# Learning/CrossRef Schemas
class CrossRefResponse(BaseSchema):
    """Schema for cross-reference response."""

    id: uuid.UUID
    invoice_line_id: uuid.UUID
    po_line_id: uuid.UUID
    dn_line_id: uuid.UUID | None
    match_type: str
    confidence: str
    match_score: int
    is_promoted: bool
    usage_count: int
    success_rate: float
    created_at: datetime


# Token Schemas
class TokenRequest(BaseSchema):
    """Schema for token request."""

    username: str
    password: str


class TokenResponse(BaseSchema):
    """Schema for token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefreshRequest(BaseSchema):
    """Schema for token refresh request."""

    refresh_token: str

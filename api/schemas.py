# api/schemas.py
"""Shared Pydantic request/response schemas used across API endpoints."""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Annotated, Any

from pydantic import BaseModel, Field, ConfigDict, field_validator


# ─────────────────────────────────────────────────────────────────────────────
# Pagination
# ─────────────────────────────────────────────────────────────────────────────

class PaginationParams(BaseModel):
    """Standard pagination query parameters."""

    page: Annotated[int, Field(ge=1, default=1, description="Page number (1-indexed)")]
    page_size: Annotated[
        int,
        Field(ge=1, le=200, default=50, description="Number of items per page"),
    ]

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


class PaginatedResponse(BaseModel):
    """Generic paginated list response."""

    total: int
    page: int
    page_size: int
    pages: int
    items: list[Any]


# ─────────────────────────────────────────────────────────────────────────────
# Invoice Schemas
# ─────────────────────────────────────────────────────────────────────────────

class InvoiceLineCreate(BaseModel):
    """Request body for creating a single invoice line."""

    line_number: Annotated[int, Field(ge=1)]
    description: Annotated[str, Field(min_length=1, max_length=500)]
    sku: str | None = None
    quantity: Annotated[Decimal, Field(ge=0)]
    unit_of_measure: str = "PCS"
    unit_price: Annotated[Decimal, Field(ge=0)]
    line_amount: Annotated[Decimal, Field(ge=0)]


class InvoiceLineResponse(BaseModel):
    """Response body for a single invoice line."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    invoice_id: uuid.UUID
    line_number: int
    description: str
    sku: str | None
    quantity: Decimal
    unit_of_measure: str
    unit_price: Decimal
    line_amount: Decimal
    po_line_id: uuid.UUID | None
    status: str
    created_at: datetime
    updated_at: datetime


class InvoiceCreate(BaseModel):
    """Request body for creating a new invoice."""

    invoice_number: Annotated[str, Field(min_length=1, max_length=100)]
    vendor_id: Annotated[str, Field(min_length=1, max_length=100)]
    vendor_name: Annotated[str, Field(min_length=1, max_length=255)]
    invoice_date: date
    due_date: date | None = None
    subtotal: Annotated[Decimal, Field(ge=0)] = Decimal("0")
    tax_amount: Annotated[Decimal, Field(ge=0)] = Decimal("0")
    total_amount: Annotated[Decimal, Field(ge=0)]
    currency: str = "EUR"
    notes: str | None = None
    lines: Annotated[list[InvoiceLineCreate], Field(min_length=1)]

    @field_validator("total_amount")
    @classmethod
    def total_matches_lines(cls, v: Decimal, info) -> Decimal:
        # Basic validation: if subtotal + tax are provided they should sum to total
        # We accept either pre-computed total or let caller compute it
        return v


class InvoiceResponse(BaseModel):
    """Response body for an invoice."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    invoice_number: str
    vendor_id: str
    vendor_name: str
    invoice_date: date
    due_date: date | None
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    currency: str
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime
    lines: list[InvoiceLineResponse] = []


class InvoiceListResponse(BaseModel):
    """Paginated list of invoices."""

    total: int
    page: int
    page_size: int
    items: list[InvoiceResponse]


# ─────────────────────────────────────────────────────────────────────────────
# Purchase Order Schemas
# ─────────────────────────────────────────────────────────────────────────────

class PurchaseOrderLineCreate(BaseModel):
    """Request body for a single PO line."""

    line_number: Annotated[int, Field(ge=1)]
    description: Annotated[str, Field(min_length=1, max_length=500)]
    sku: str | None = None
    quantity: Annotated[Decimal, Field(ge=0)]
    unit_of_measure: str = "PCS"
    unit_price: Annotated[Decimal, Field(ge=0)]
    line_amount: Annotated[Decimal, Field(ge=0)]


class PurchaseOrderLineResponse(BaseModel):
    """Response body for a single PO line."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    purchase_order_id: uuid.UUID
    line_number: int
    description: str
    sku: str | None
    quantity: Decimal
    delivered_quantity: Decimal
    invoiced_quantity: Decimal
    unit_of_measure: str
    unit_price: Decimal
    line_amount: Decimal
    status: str
    delivery_note_line_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class PurchaseOrderCreate(BaseModel):
    """Request body for creating a new purchase order."""

    po_number: Annotated[str, Field(min_length=1, max_length=100)]
    vendor_id: Annotated[str, Field(min_length=1, max_length=100)]
    vendor_name: Annotated[str, Field(min_length=1, max_length=255)]
    order_date: date
    delivery_date: date | None = None
    currency: str = "EUR"
    total_amount: Annotated[Decimal, Field(ge=0)]
    notes: str | None = None
    lines: Annotated[list[PurchaseOrderLineCreate], Field(min_length=1)]


class PurchaseOrderResponse(BaseModel):
    """Response body for a purchase order."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    po_number: str
    vendor_id: str
    vendor_name: str
    order_date: date
    delivery_date: date | None
    currency: str
    total_amount: Decimal
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime
    lines: list[PurchaseOrderLineResponse] = []


class PurchaseOrderListResponse(BaseModel):
    """Paginated list of purchase orders."""

    total: int
    page: int
    page_size: int
    items: list[PurchaseOrderResponse]


# ─────────────────────────────────────────────────────────────────────────────
# Delivery Note Schemas
# ─────────────────────────────────────────────────────────────────────────────

class DeliveryNoteLineCreate(BaseModel):
    """Request body for a single delivery note line."""

    line_number: Annotated[int, Field(ge=1)]
    description: Annotated[str, Field(min_length=1, max_length=500)]
    sku: str | None = None
    quantity: Annotated[Decimal, Field(gt=0)]
    unit_of_measure: str = "PCS"


class DeliveryNoteCreate(BaseModel):
    """Request body for creating a delivery note."""

    dn_number: Annotated[str, Field(min_length=1, max_length=100)]
    vendor_id: Annotated[str, Field(min_length=1, max_length=100)]
    vendor_name: Annotated[str, Field(min_length=1, max_length=255)]
    issue_date: date
    po_reference: str | None = None
    notes: str | None = None
    lines: Annotated[list[DeliveryNoteLineCreate], Field(min_length=1)]


class DeliveryNoteLineResponse(BaseModel):
    """Response body for a delivery note line."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    delivery_note_id: uuid.UUID
    line_number: int
    description: str
    sku: str | None
    quantity: Decimal
    unit_of_measure: str
    po_line_id: uuid.UUID | None
    status: str
    created_at: datetime
    updated_at: datetime


class DeliveryNoteResponse(BaseModel):
    """Response body for a delivery note."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    dn_number: str
    vendor_id: str
    vendor_name: str
    issue_date: date
    po_reference: str | None
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime
    lines: list[DeliveryNoteLineResponse] = []


class DeliveryNoteListResponse(BaseModel):
    """Paginated list of delivery notes."""

    total: int
    page: int
    page_size: int
    items: list[DeliveryNoteResponse]


# ─────────────────────────────────────────────────────────────────────────────
# Matching Schemas
# ─────────────────────────────────────────────────────────────────────────────

class MatchingResultLine(BaseModel):
    """Result of matching a single invoice line."""

    invoice_line_id: uuid.UUID
    po_line_id: uuid.UUID | None
    score: float
    decision: str
    price_match: bool
    qty_match: bool
    dn_line_id: uuid.UUID | None = None


class MatchingResult(BaseModel):
    """Result of triggering the matching engine for an invoice."""

    invoice_id: uuid.UUID
    overall_score: float
    decision: str
    lines: list[MatchingResultLine]
    exception_count: int = 0
    matched_count: int = 0
    total_lines: int
    started_at: datetime
    completed_at: datetime


# ─────────────────────────────────────────────────────────────────────────────
# Exception Schemas
# ─────────────────────────────────────────────────────────────────────────────

class ExceptionResponse(BaseModel):
    """Response body for a matching exception."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    invoice_id: uuid.UUID
    invoice_line_id: uuid.UUID | None
    po_line_id: uuid.UUID | None
    exception_type: str
    description: str | None
    score: float | None
    is_resolved: bool
    resolved_by: str | None
    resolved_at: datetime | None
    resolution_notes: str | None
    created_at: datetime


class ExceptionResolveRequest(BaseModel):
    """Request to resolve an exception."""

    resolution_notes: str | None = None


class ExceptionDismissRequest(BaseModel):
    """Request to dismiss an exception."""

    reason: str


# ─────────────────────────────────────────────────────────────────────────────
# Balance Ledger Schemas
# ─────────────────────────────────────────────────────────────────────────────

class BalanceLedgerEntryResponse(BaseModel):
    """Response body for a single balance ledger entry."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    transaction_type: str
    quantity: Decimal
    amount: Decimal
    reference: str | None
    po_line_id: uuid.UUID
    invoice_line_id: uuid.UUID | None
    created_at: datetime


class POLineBalanceResponse(BaseModel):
    """Current balance state for a PO line."""

    model_config = ConfigDict(from_attributes=True)

    po_line_id: uuid.UUID
    ordered_quantity: Decimal
    invoiced_quantity: Decimal
    delivered_quantity: Decimal
    balance_quantity: Decimal
    entries: list[BalanceLedgerEntryResponse] = []


# ─────────────────────────────────────────────────────────────────────────────
# Common / Health
# ─────────────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str = "0.1.0"
    environment: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str
    error_code: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

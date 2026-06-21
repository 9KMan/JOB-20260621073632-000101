# api/schemas.py
"""Shared Pydantic request/response schemas for the API."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ── Generic Pagination ────────────────────────────────────────────────────────

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated list response."""

    items: list[T]
    total: int = Field(ge=0)
    page: int = Field(ge=1, default=1)
    page_size: int = Field(ge=1, le=100, default=20)
    pages: int = Field(ge=0)

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        """Factory to build a paginated response."""
        pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)


# ── Invoice Schemas ───────────────────────────────────────────────────────────


class InvoiceLineCreate(BaseModel):
    """Schema for creating an invoice line."""

    line_number: int = Field(ge=1)
    description: str | None = None
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    line_amount: Decimal = Field(ge=0)
    product_code: str | None = None


class InvoiceLineResponse(InvoiceLineCreate):
    """Schema for an invoice line in responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    po_line_id: UUID | None = None
    match_score: float | None = None
    is_matched: bool
    created_at: datetime


class InvoiceCreate(BaseModel):
    """Schema for ingesting a new invoice."""

    invoice_number: str = Field(min_length=1, max_length=50)
    vendor_code: str = Field(min_length=1, max_length=50)
    vendor_name: str | None = None
    vendor_tax_id: str | None = None
    currency: str = Field(default="USD", min_length=3, max_length=3)
    subtotal: Decimal = Field(default=Decimal("0"))
    tax_amount: Decimal = Field(default=Decimal("0"))
    total_amount: Decimal
    invoice_date: date | None = None
    due_date: date | None = None
    received_date: date | None = None
    notes: str | None = None
    lines: list[InvoiceLineCreate] = Field(min_length=1)

    @field_validator("currency")
    @classmethod
    def currency_upper(cls, v: str) -> str:
        return v.upper()


class InvoiceUpdate(BaseModel):
    """Schema for updating an invoice."""

    status: str | None = None
    notes: str | None = None
    due_date: date | None = None


class InvoiceResponse(BaseModel):
    """Schema for invoice responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    invoice_number: str
    vendor_code: str
    vendor_name: str | None
    currency: str
    total_amount: Decimal
    status: str
    match_decision: str | None
    match_score: float | None
    matched_po_id: UUID | None
    received_date: date | None
    lines: list[InvoiceLineResponse] = []
    created_at: datetime


# ── Purchase Order Schemas ─────────────────────────────────────────────────────


class POLineCreate(BaseModel):
    """Schema for creating a PO line."""

    line_number: int = Field(ge=1)
    description: str | None = None
    quantity_ordered: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    line_amount: Decimal = Field(ge=0)
    product_code: str | None = None


class POLineResponse(POLineCreate):
    """Schema for a PO line in responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    quantity_received: Decimal
    quantity_invoiced: Decimal
    created_at: datetime


class PurchaseOrderCreate(BaseModel):
    """Schema for ingesting a new purchase order."""

    po_number: str = Field(min_length=1, max_length=50)
    vendor_code: str = Field(min_length=1, max_length=50)
    vendor_name: str | None = None
    vendor_tax_id: str | None = None
    currency: str = Field(default="USD", min_length=3, max_length=3)
    subtotal: Decimal = Field(default=Decimal("0"))
    tax_amount: Decimal = Field(default=Decimal("0"))
    total_amount: Decimal
    po_date: date | None = None
    expected_delivery_date: date | None = None
    notes: str | None = None
    lines: list[POLineCreate] = Field(min_length=1)

    @field_validator("currency")
    @classmethod
    def currency_upper(cls, v: str) -> str:
        return v.upper()


class PurchaseOrderResponse(BaseModel):
    """Schema for PO responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    po_number: str
    vendor_code: str
    vendor_name: str | None
    currency: str
    total_amount: Decimal
    status: str
    po_date: date | None
    lines: list[POLineResponse] = []
    created_at: datetime


# ── Delivery Note Schemas ──────────────────────────────────────────────────────


class DeliveryNoteLineCreate(BaseModel):
    """Schema for creating a delivery note line."""

    line_number: int = Field(ge=1)
    description: str | None = None
    quantity_delivered: Decimal = Field(gt=0)
    product_code: str | None = None


class DeliveryNoteLineResponse(DeliveryNoteLineCreate):
    """Schema for a DN line in responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    po_line_id: UUID | None = None
    invoice_line_id: UUID | None = None
    is_matched: bool
    match_score: float | None
    created_at: datetime


class DeliveryNoteCreate(BaseModel):
    """Schema for ingesting a delivery note."""

    dn_number: str = Field(min_length=1, max_length=50)
    vendor_code: str = Field(min_length=1, max_length=50)
    vendor_name: str | None = None
    po_number: str | None = None
    currency: str = Field(default="USD", min_length=3, max_length=3)
    dn_date: date | None = None
    received_date: date | None = None
    notes: str | None = None
    lines: list[DeliveryNoteLineCreate] = Field(min_length=1)

    @field_validator("currency")
    @classmethod
    def currency_upper(cls, v: str) -> str:
        return v.upper()


class DeliveryNoteResponse(BaseModel):
    """Schema for delivery note responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dn_number: str
    vendor_code: str
    vendor_name: str | None
    po_number: str | None
    currency: str
    status: str
    dn_date: date | None
    lines: list[DeliveryNoteLineResponse] = []
    created_at: datetime


# ── Matching Schemas ───────────────────────────────────────────────────────────


class MatchTriggerRequest(BaseModel):
    """Request to trigger matching for an invoice."""

    invoice_id: UUID
    force_rematch: bool = False


class MatchLineResult(BaseModel):
    """Result of matching a single invoice line."""

    invoice_line_id: UUID
    po_line_id: UUID | None
    match_score: float
    is_within_price_tolerance: bool
    is_within_qty_tolerance: bool
    decision: str
    decision_reason: str | None


class MatchResultResponse(BaseModel):
    """Result of the full matching process for an invoice."""

    invoice_id: UUID
    overall_score: float
    decision: str
    line_results: list[MatchLineResult]
    exception_count: int = 0
    auto_approved: bool = False
    matched_po_id: UUID | None


# ── Exception Schemas ─────────────────────────────────────────────────────────


class ExceptionResolveRequest(BaseModel):
    """Request to resolve an exception."""

    resolution_notes: str | None = None
    resolved_po_line_id: UUID | None = None


class ExceptionDismissRequest(BaseModel):
    """Request to dismiss an exception."""

    dismissal_reason: str


class ExceptionResponse(BaseModel):
    """Schema for exception responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    invoice_id: UUID
    invoice_line_id: UUID | None
    po_line_id: UUID | None
    exception_type: str
    status: str
    match_score: float | None
    resolution_notes: str | None
    created_at: datetime


# ── Balance Ledger Schemas ─────────────────────────────────────────────────────


class BalanceLedgerResponse(BaseModel):
    """Schema for balance ledger entries."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    po_line_id: UUID
    invoice_id: UUID | None
    quantity_balance: Decimal
    amount_balance: Decimal
    is_closed: bool
    updated_at: datetime


# ── Common Schemas ─────────────────────────────────────────────────────────────


class SuccessResponse(BaseModel):
    """Generic success response."""

    success: bool = True
    message: str
    detail: Any = None


class ErrorResponse(BaseModel):
    """Generic error response."""

    success: bool = False
    error: str
    detail: Any = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    environment: str
    database: str | None = None

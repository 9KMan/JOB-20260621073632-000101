// api/schemas.py
"""Shared Pydantic schemas for request/response models.

These schemas are used across multiple API endpoints for
common data structures.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field


class PaginationParams(BaseModel):
    """Standard pagination parameters."""

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


class PaginatedResponse(BaseModel):
    """Standard paginated response wrapper."""

    items: list[dict]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(
        cls,
        items: list[dict],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse":
        """Create a paginated response."""
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields in responses."""

    created_at: datetime
    updated_at: datetime


class UUIDMixin(BaseModel):
    """Mixin for UUID id field."""

    id: UUID


# Invoice Schemas
class InvoiceLineBase(BaseModel):
    """Base schema for invoice line."""

    line_number: int
    description: str = Field(max_length=500)
    sku: str | None = None
    quantity: Decimal = Field(ge=0)
    unit_price: Decimal = Field(ge=0)
    line_amount: Decimal = Field(ge=0)


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating an invoice line."""

    pass


class InvoiceLineResponse(InvoiceLineBase, TimestampMixin):
    """Schema for invoice line response."""

    id: UUID
    invoice_id: UUID
    matched_po_line_id: UUID | None = None
    match_status: str | None = None
    match_score: float | None = None

    model_config = ConfigDict(from_attributes=True)


class InvoiceBase(BaseModel):
    """Base schema for invoice."""

    vendor_code: str = Field(max_length=50)
    vendor_name: str = Field(max_length=255)
    invoice_number: str = Field(max_length=100)
    invoice_date: date
    total_amount: Decimal = Field(ge=0)
    tax_amount: Decimal | None = None
    currency: str = Field(default="USD", max_length=3)
    due_date: date | None = None
    payment_terms: str | None = None
    notes: str | None = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating an invoice."""

    lines: list[InvoiceLineCreate] = Field(min_length=1)


class InvoiceUpdate(BaseModel):
    """Schema for updating an invoice."""

    status: str | None = None
    notes: str | None = None
    due_date: date | None = None


class InvoiceResponse(InvoiceBase, TimestampMixin):
    """Schema for invoice response."""

    id: UUID
    status: str
    matched_po_id: UUID | None = None
    match_score: float | None = None
    match_decision: str | None = None
    matched_at: datetime | None = None
    lines: list[InvoiceLineResponse] = []

    model_config = ConfigDict(from_attributes=True)


# Purchase Order Schemas
class POLineBase(BaseModel):
    """Base schema for PO line."""

    line_number: int
    description: str = Field(max_length=500)
    sku: str | None = None
    manufacturer_part: str | None = None
    ordered_quantity: Decimal = Field(ge=0)
    unit_price: Decimal = Field(ge=0)
    line_amount: Decimal = Field(ge=0)


class POLineCreate(POLineBase):
    """Schema for creating a PO line."""

    pass


class POLineResponse(POLineBase, TimestampMixin):
    """Schema for PO line response."""

    id: UUID
    po_id: UUID
    delivered_quantity: Decimal = Decimal("0")
    invoiced_quantity: Decimal = Decimal("0")

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderBase(BaseModel):
    """Base schema for purchase order."""

    po_number: str = Field(max_length=50)
    vendor_code: str = Field(max_length=50)
    vendor_name: str = Field(max_length=255)
    department_code: str | None = None
    po_date: date
    expected_delivery_date: date | None = None
    total_amount: Decimal = Field(ge=0)
    currency: str = Field(default="USD", max_length=3)
    notes: str | None = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a purchase order."""

    lines: list[POLineCreate] = Field(min_length=1)


class PurchaseOrderResponse(PurchaseOrderBase, TimestampMixin):
    """Schema for purchase order response."""

    id: UUID
    status: str
    erp_reference: str | None = None
    lines: list[POLineResponse] = []

    model_config = ConfigDict(from_attributes=True)


# Delivery Note Schemas
class DNLineBase(BaseModel):
    """Base schema for DN line."""

    line_number: int
    description: str = Field(max_length=500)
    sku: str | None = None
    delivered_quantity: Decimal = Field(ge=0)


class DNLineCreate(DNLineBase):
    """Schema for creating a DN line."""

    pass


class DNLineResponse(DNLineBase, TimestampMixin):
    """Schema for DN line response."""

    id: UUID
    dn_id: UUID
    matched_po_line_id: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class DeliveryNoteBase(BaseModel):
    """Base schema for delivery note."""

    dn_number: str = Field(max_length=100)
    vendor_code: str = Field(max_length=50)
    vendor_name: str = Field(max_length=255)
    po_number: str | None = None
    dn_date: date
    receipt_date: date
    notes: str | None = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating a delivery note."""

    lines: list[DNLineCreate] = Field(min_length=1)


class DeliveryNoteResponse(DeliveryNoteBase, TimestampMixin):
    """Schema for delivery note response."""

    id: UUID
    status: str
    source: str = "manual"
    lines: list[DNLineResponse] = []

    model_config = ConfigDict(from_attributes=True)


# Matching Schemas
class MatchingResult(BaseModel):
    """Result of a matching operation."""

    invoice_id: UUID
    status: str
    match_score: float
    decision: str
    matched_po_id: UUID | None = None
    line_matches: list[dict] = []
    exceptions: list[dict] = []


class MatchingDecision(BaseModel):
    """Matching decision with detailed breakdown."""

    invoice_id: UUID
    overall_score: float
    decision: str
    decision_type: str
    threshold_high: int
    threshold_mid: int
    threshold_low: int
    line_scores: list[dict]
    recommended_action: str


class MatchConfirmationInput(BaseModel):
    """Input for confirming or rejecting a match."""

    match_id: str
    confirmed: bool
    source: str = "manual"
    notes: str | None = None


# Exception Schemas
class ExceptionBase(BaseModel):
    """Base schema for exception."""

    reason: str
    description: str | None = None


class ExceptionResponse(BaseModel):
    """Schema for exception response."""

    id: UUID
    invoice_id: UUID
    po_id: UUID | None = None
    reason: str
    status: str
    description: str | None = None
    created_at: datetime
    resolved_at: datetime | None = None
    resolved_by: str | None = None
    resolution_notes: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ExceptionResolveInput(BaseModel):
    """Input for resolving an exception."""

    resolution_notes: str | None = None
    override_amount: Decimal | None = None


class ExceptionDismissInput(BaseModel):
    """Input for dismissing an exception."""

    reason: str
    notes: str | None = None


# Balance Ledger Schemas
class BalanceLedgerResponse(BaseModel):
    """Schema for balance ledger response."""

    po_id: UUID
    po_line_id: UUID
    ordered_qty: Decimal
    delivered_qty: Decimal
    invoiced_qty: Decimal
    approved_invoiced_qty: Decimal
    remaining_to_deliver: Decimal
    remaining_to_invoice: Decimal
    pending_approval_qty: Decimal
    last_delivery_date: datetime | None = None
    last_invoice_date: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# CrossRef Schemas
class CrossRefResponse(BaseModel):
    """Schema for cross-reference response."""

    id: UUID
    vendor_code: str
    vendor_name: str
    sku: str | None = None
    po_description: str
    unit_price: float
    match_count: int
    avg_match_score: float
    confirmation: str
    success_rate: float

    model_config = ConfigDict(from_attributes=True)


# Health Check
class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str
    timestamp: datetime
    database: str = "connected"


# Error Response
class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    detail: str | None = None
    status_code: int

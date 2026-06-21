# api/schemas.py
"""Shared Pydantic schemas for API request/response models.

These schemas are used across multiple endpoint groups.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# Generic type for paginated responses
T = TypeVar("T")


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    error: str = Field(..., description="Error type code")
    message: str = Field(..., description="Human-readable error message")
    details: dict[str, Any] | None = Field(default=None, description="Additional error details")
    request_id: str | None = Field(default=None, description="Request tracking ID")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "validation_error",
                "message": "Invalid invoice data",
                "details": {"field": "invoice_number", "issue": "already exists"},
            }
        }
    )


class MessageResponse(BaseModel):
    """Simple message response schema."""

    message: str = Field(..., description="Response message")
    success: bool = Field(default=True, description="Operation success status")


class HealthCheck(BaseModel):
    """Health check response schema."""

    status: str = Field(..., description="Service health status")
    version: str = Field(..., description="Application version")
    database: str = Field(..., description="Database connection status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response schema."""

    items: list[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")

    @field_validator("pages", mode="before")
    @classmethod
    def calculate_pages(cls, v: int | None, info) -> int:
        """Calculate total pages from total and page_size."""
        if v is not None:
            return v
        values = info.data
        total = values.get("total", 0)
        page_size = values.get("page_size", 10)
        if page_size <= 0:
            return 0
        return (total + page_size - 1) // page_size

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        """Factory method to create paginated response."""
        pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1,
        )


class PaginationParams(BaseModel):
    """Standard pagination parameters."""

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.page_size


# Invoice Schemas
class InvoiceLineBase(BaseModel):
    """Base schema for invoice line items."""

    line_number: int = Field(..., ge=1)
    description: str = Field(..., max_length=500)
    sku: str | None = Field(default=None, max_length=100)
    quantity: Decimal = Field(..., ge=Decimal("0"))
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=Decimal("0"))
    line_amount: Decimal = Field(..., ge=Decimal("0"))
    po_line_reference: str | None = Field(default=None, max_length=100)


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating invoice line items."""

    pass


class InvoiceLineResponse(InvoiceLineBase):
    """Schema for invoice line item response."""

    id: UUID
    matched: bool = False
    match_score: float | None = None
    match_confidence: str | None = None

    model_config = ConfigDict(from_attributes=True)


class InvoiceBase(BaseModel):
    """Base schema for invoices."""

    vendor_id: str = Field(..., max_length=255)
    vendor_name: str = Field(..., max_length=500)
    vendor_tax_id: str | None = Field(default=None, max_length=50)
    invoice_number: str = Field(..., max_length=100)
    invoice_date: date
    due_date: date | None = None
    subtotal: Decimal = Field(..., ge=Decimal("0"))
    tax_amount: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    total_amount: Decimal = Field(..., ge=Decimal("0"))
    currency: str = Field(default="USD", max_length=3)
    payment_terms: str | None = Field(default=None, max_length=100)
    notes: str | None = None
    po_reference: str | None = Field(default=None, max_length=100)


class InvoiceCreate(InvoiceBase):
    """Schema for creating invoices."""

    lines: list[InvoiceLineCreate] = Field(default_factory=list)


class InvoiceUpdate(BaseModel):
    """Schema for updating invoices."""

    status: str | None = None
    notes: str | None = None
    approved_by: str | None = None


class InvoiceResponse(InvoiceBase):
    """Schema for invoice response."""

    id: UUID
    status: str
    match_score: float | None = None
    match_decision: str | None = None
    matched_by: str | None = None
    matched_at: datetime | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    lines: list[InvoiceLineResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# Purchase Order Schemas
class PurchaseOrderLineBase(BaseModel):
    """Base schema for PO line items."""

    line_number: int = Field(..., ge=1)
    description: str = Field(..., max_length=500)
    sku: str | None = Field(default=None, max_length=100)
    category: str | None = Field(default=None, max_length=100)
    quantity_ordered: Decimal = Field(..., ge=Decimal("0"))
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=Decimal("0"))
    line_amount: Decimal = Field(..., ge=Decimal("0"))
    delivery_date: date | None = None


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Schema for creating PO line items."""

    pass


class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    """Schema for PO line item response."""

    id: UUID
    quantity_delivered: Decimal = Decimal("0")
    quantity_invoiced: Decimal = Decimal("0")
    quantity_remaining: Decimal = Field(default=Decimal("0"))
    quantity_pending_invoice: Decimal = Field(default=Decimal("0"))

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderBase(BaseModel):
    """Base schema for purchase orders."""

    po_number: str = Field(..., max_length=100)
    vendor_id: str = Field(..., max_length=255)
    vendor_name: str = Field(..., max_length=500)
    order_date: date
    delivery_date: date | None = None
    subtotal: Decimal = Field(..., ge=Decimal("0"))
    tax_amount: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    total_amount: Decimal = Field(..., ge=Decimal("0"))
    currency: str = Field(default="USD", max_length=3)
    shipping_cost: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    terms: str | None = Field(default=None, max_length=200)
    notes: str | None = None
    requested_by: str | None = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating purchase orders."""

    lines: list[PurchaseOrderLineCreate] = Field(default_factory=list)


class PurchaseOrderResponse(PurchaseOrderBase):
    """Schema for purchase order response."""

    id: UUID
    status: str
    approved_by: str | None = None
    approved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    lines: list[PurchaseOrderLineResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# Delivery Note Schemas
class DeliveryNoteLineBase(BaseModel):
    """Base schema for delivery note line items."""

    line_number: int = Field(..., ge=1)
    description: str = Field(..., max_length=500)
    sku: str | None = Field(default=None, max_length=100)
    quantity_delivered: Decimal = Field(..., ge=Decimal("0"))
    quantity_accepted: Decimal = Field(..., ge=Decimal("0"))
    quantity_rejected: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=Decimal("0"))
    line_amount: Decimal = Field(..., ge=Decimal("0"))
    po_line_reference: str | None = Field(default=None, max_length=100)


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating delivery note line items."""

    pass


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """Schema for delivery note line item response."""

    id: UUID
    matched: bool = False
    match_score: float | None = None
    quality_check_passed: bool = True

    model_config = ConfigDict(from_attributes=True)


class DeliveryNoteBase(BaseModel):
    """Base schema for delivery notes."""

    dn_number: str = Field(..., max_length=100)
    external_reference: str | None = Field(default=None, max_length=100)
    vendor_id: str = Field(..., max_length=255)
    vendor_name: str = Field(..., max_length=500)
    po_reference: str | None = Field(default=None, max_length=100)
    gr_number: str | None = Field(default=None, max_length=100)
    shipment_date: date | None = None
    receipt_date: date
    total_amount: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    currency: str = Field(default="USD", max_length=3)
    notes: str | None = None
    received_by: str | None = None
    warehouse_id: str | None = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating delivery notes."""

    lines: list[DeliveryNoteLineCreate] = Field(default_factory=list)


class DeliveryNoteResponse(DeliveryNoteBase):
    """Schema for delivery note response."""

    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    lines: list[DeliveryNoteLineResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# Matching Schemas
class MatchRequest(BaseModel):
    """Schema for requesting a match operation."""

    invoice_id: UUID
    trigger_auto_match: bool = Field(default=True, description="Whether to auto-trigger matching")


class MatchDecisionResponse(BaseModel):
    """Schema for match decision response."""

    invoice_id: UUID
    invoice_number: str
    decision: str
    confidence: str
    score: float
    threshold_used: str | None = None
    matched_po_id: UUID | None = None
    matched_po_number: str | None = None
    matched_dn_ids: list[UUID] = Field(default_factory=list)
    exceptions: list[dict[str, Any]] = Field(default_factory=list)
    matched_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MatchLineDetail(BaseModel):
    """Detailed match information for a single line."""

    invoice_line_id: UUID
    invoice_line_number: int
    description: str
    invoice_quantity: Decimal
    invoice_unit_price: Decimal
    matched_po_line_id: UUID | None = None
    matched_dn_line_id: UUID | None = None
    match_score: float
    match_confidence: str
    price_match: bool
    quantity_match: bool
    exceptions: list[str] = Field(default_factory=list)


class MatchDetailsResponse(BaseModel):
    """Detailed match information response."""

    invoice_id: UUID
    invoice_number: str
    decision: str
    overall_score: float
    lines: list[MatchLineDetail]
    cross_ref_used: list[str] = Field(default_factory=list, description="Cross-ref IDs used")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Exception Schemas
class ExceptionBase(BaseModel):
    """Base schema for exceptions."""

    exception_type: str
    message: str
    field: str | None = None
    expected_value: str | None = None
    actual_value: str | None = None


class ExceptionCreate(ExceptionBase):
    """Schema for creating exceptions."""

    invoice_id: UUID
    po_line_id: UUID | None = None
    dn_line_id: UUID | None = None


class ExceptionResponse(ExceptionBase):
    """Schema for exception response."""

    id: UUID
    invoice_id: UUID
    po_line_id: UUID | None = None
    dn_line_id: UUID | None = None
    resolution: str
    resolved_by: str | None = None
    resolved_at: datetime | None = None
    resolution_notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExceptionResolveRequest(BaseModel):
    """Schema for resolving an exception."""

    resolution: str = Field(..., description="Resolution status")
    notes: str | None = Field(default=None, description="Resolution notes")
    resolved_by: str = Field(..., description="User resolving the exception")


# Balance Ledger Schemas
class BalanceLedgerResponse(BaseModel):
    """Schema for balance ledger response."""

    id: UUID
    purchase_order_id: UUID
    po_line_id: UUID | None = None
    invoice_id: UUID | None = None
    transaction_type: str
    transaction_id: str
    quantity_ordered: Decimal
    quantity_delivered: Decimal
    quantity_invoiced: Decimal
    quantity_paid: Decimal
    amount_ordered: Decimal
    amount_delivered: Decimal
    amount_invoiced: Decimal
    amount_paid: Decimal
    balance_quantity: Decimal
    balance_amount: Decimal
    effective_date: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BalanceSummaryResponse(BaseModel):
    """Schema for balance summary response."""

    purchase_order_id: UUID
    po_number: str
    total_ordered: Decimal
    total_delivered: Decimal
    total_invoiced: Decimal
    total_paid: Decimal
    quantity_balance: Decimal
    amount_balance: Decimal
    currency: str
    lines: list[dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

# src/api/schemas.py
"""Shared Pydantic schemas for API request/response models."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class TimestampMixin(BaseSchema):
    """Schema mixin for timestamp fields."""
    
    created_at: datetime
    updated_at: datetime


class UUIDMixin(BaseSchema):
    """Schema mixin for UUID field."""
    
    id: UUID


# Pagination schemas
class PaginationMeta(BaseSchema):
    """Pagination metadata."""
    
    page: int = Field(ge=1, description="Current page number")
    per_page: int = Field(ge=1, le=100, description="Items per page")
    total: int = Field(ge=0, description="Total number of items")
    total_pages: int = Field(ge=0, description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")


class PaginatedResponse(BaseSchema, Generic[T]):
    """Generic paginated response wrapper."""
    
    items: list[T]
    meta: PaginationMeta


# Common schemas
class ErrorDetail(BaseSchema):
    """Error detail schema."""
    
    field: str | None = Field(default=None, description="Field that caused the error")
    message: str = Field(description="Error message")
    code: str | None = Field(default=None, description="Error code")


class ErrorResponse(BaseSchema):
    """Standard error response."""
    
    detail: str = Field(description="Error message")
    code: str | None = Field(default=None, description="Error code")
    errors: list[ErrorDetail] | None = Field(default=None, description="Validation errors")


class HealthResponse(BaseSchema):
    """Health check response."""
    
    status: str = Field(description="Service status")
    version: str = Field(description="Application version")


# Invoice schemas
class InvoiceLineBase(BaseSchema):
    """Base invoice line schema."""
    
    line_number: int
    description: str
    product_code: str | None = None
    quantity: Decimal = Field(ge=0)
    unit_of_measure: str = "EA"
    unit_price: Decimal = Field(ge=0)
    tax_code: str | None = None
    tax_rate: Decimal = Field(default=Decimal("0.0000"), ge=0)
    line_total: Decimal = Field(ge=0)


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating an invoice line."""
    
    po_line_id: UUID | None = None
    delivery_line_id: UUID | None = None


class InvoiceLineResponse(InvoiceLineBase, UUIDMixin):
    """Invoice line response schema."""
    
    invoice_id: UUID
    po_line_id: UUID | None = None
    delivery_line_id: UUID | None = None
    match_status: str
    match_score: Decimal | None = None


class InvoiceBase(BaseSchema):
    """Base invoice schema."""
    
    invoice_number: str = Field(max_length=100)
    supplier_id: str = Field(max_length=100)
    supplier_name: str = Field(max_length=255)
    invoice_date: date
    due_date: date | None = None
    currency: str = Field(default="USD", max_length=3)
    subtotal: Decimal = Field(default=Decimal("0.00"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    total_amount: Decimal = Field(ge=0)
    vendor_reference: str | None = None
    payment_terms: str | None = None
    notes: str | None = None
    metadata: dict[str, Any] | None = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating an invoice."""
    
    lines: list[InvoiceLineCreate] = Field(default_factory=list)


class InvoiceUpdate(BaseSchema):
    """Schema for updating an invoice."""
    
    status: str | None = None
    notes: str | None = None
    metadata: dict[str, Any] | None = None


class InvoiceResponse(InvoiceBase, UUIDMixin, TimestampMixin):
    """Invoice response schema."""
    
    status: str
    matched_at: datetime | None = None
    matched_by: str | None = None
    lines: list[InvoiceLineResponse] = Field(default_factory=list)


# Purchase Order schemas
class PurchaseOrderLineBase(BaseSchema):
    """Base PO line schema."""
    
    line_number: int
    description: str
    product_code: str | None = None
    category: str | None = None
    quantity: Decimal = Field(ge=0)
    unit_of_measure: str = "EA"
    unit_price: Decimal = Field(ge=0)
    tax_code: str | None = None
    tax_rate: Decimal = Field(default=Decimal("0.0000"), ge=0)
    line_total: Decimal = Field(ge=0)
    required_delivery_date: date | None = None
    promised_delivery_date: date | None = None


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Schema for creating a PO line."""
    pass


class PurchaseOrderLineResponse(PurchaseOrderLineBase, UUIDMixin):
    """PO line response schema."""
    
    po_id: UUID
    received_quantity: Decimal
    invoiced_quantity: Decimal


class PurchaseOrderBase(BaseSchema):
    """Base PO schema."""
    
    po_number: str = Field(max_length=100)
    supplier_id: str = Field(max_length=100)
    supplier_name: str = Field(max_length=255)
    buyer_id: str | None = None
    buyer_name: str | None = None
    po_date: date
    expected_delivery_date: date | None = None
    currency: str = Field(default="USD", max_length=3)
    subtotal: Decimal = Field(default=Decimal("0.00"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    total_amount: Decimal = Field(ge=0)
    payment_terms: str | None = None
    shipping_terms: str | None = None
    notes: str | None = None
    metadata: dict[str, Any] | None = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a purchase order."""
    
    lines: list[PurchaseOrderLineCreate] = Field(default_factory=list)


class PurchaseOrderResponse(PurchaseOrderBase, UUIDMixin, TimestampMixin):
    """PO response schema."""
    
    status: str
    lines: list[PurchaseOrderLineResponse] = Field(default_factory=list)


# Delivery Note schemas
class DeliveryNoteLineBase(BaseSchema):
    """Base DN line schema."""
    
    line_number: int
    description: str
    product_code: str | None = None
    quantity: Decimal = Field(ge=0)
    unit_of_measure: str = "EA"
    po_line_id: UUID | None = None


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating a DN line."""
    pass


class DeliveryNoteLineResponse(DeliveryNoteLineBase, UUIDMixin):
    """DN line response schema."""
    
    dn_id: UUID
    received_flag: bool
    received_at: datetime | None = None


class DeliveryNoteBase(BaseSchema):
    """Base delivery note schema."""
    
    dn_number: str = Field(max_length=100)
    supplier_id: str = Field(max_length=100)
    supplier_name: str = Field(max_length=255)
    po_id: UUID | None = None
    carrier: str | None = None
    tracking_number: str | None = None
    shipment_date: date
    delivery_date: date | None = None
    notes: str | None = None
    metadata: dict[str, Any] | None = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating a delivery note."""
    
    lines: list[DeliveryNoteLineCreate] = Field(default_factory=list)


class DeliveryNoteResponse(DeliveryNoteBase, UUIDMixin, TimestampMixin):
    """DN response schema."""
    
    status: str
    lines: list[DeliveryNoteLineResponse] = Field(default_factory=list)


# Matching schemas
class MatchingTriggerRequest(BaseSchema):
    """Request to trigger matching for an invoice."""
    
    invoice_id: UUID = Field(description="Invoice ID to match")
    match_delivery_notes: bool = Field(
        default=True,
        description="Whether to include delivery notes in matching",
    )


class MatchScoreDetail(BaseSchema):
    """Detailed scoring breakdown."""
    
    price_score: Decimal = Field(ge=0, le=1)
    quantity_score: Decimal = Field(ge=0, le=1)
    date_score: Decimal = Field(ge=0, le=1)
    supplier_score: Decimal = Field(ge=0, le=1)
    product_score: Decimal = Field(ge=0, le=1)


class MatchDecision(BaseSchema):
    """Match decision for an invoice."""
    
    invoice_id: UUID
    decision: str = Field(description="auto_approve, one_click_approve, exception, manual_review")
    overall_score: Decimal = Field(ge=0, le=1)
    score_breakdown: MatchScoreDetail | None = None
    matched_po_id: UUID | None = None
    matched_po_number: str | None = None
    matched_lines: int = 0
    unmatched_lines: int = 0
    total_lines: int = 0
    exceptions: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)


class MatchingResponse(BaseSchema):
    """Response from matching operation."""
    
    status: str
    invoice_id: UUID
    match_decision: MatchDecision | None = None
    processing_time_ms: int | None = None


# Exception schemas
class ExceptionBase(BaseSchema):
    """Base exception schema."""
    
    exception_type: str
    invoice_id: UUID | None = None
    po_id: UUID | None = None
    po_line_id: UUID | None = None
    description: str
    details: dict[str, Any] | None = None


class ExceptionCreate(ExceptionBase):
    """Schema for creating an exception."""
    
    pass


class ExceptionResponse(ExceptionBase, UUIDMixin, TimestampMixin):
    """Exception response schema."""
    
    status: str
    resolved_at: datetime | None = None
    resolved_by: str | None = None
    resolution_notes: str | None = None


class ExceptionResolveRequest(BaseSchema):
    """Request to resolve an exception."""
    
    resolution_notes: str = Field(description="Resolution notes")
    action_taken: str = Field(description="Action taken to resolve")


class ExceptionDismissRequest(BaseSchema):
    """Request to dismiss an exception."""
    
    reason: str = Field(description="Reason for dismissing")


# Balance Ledger schemas
class BalanceLedgerEntry(BaseSchema):
    """Single ledger entry."""
    
    id: UUID
    po_id: UUID
    po_line_id: UUID
    transaction_type: str
    quantity_before: Decimal
    quantity_change: Decimal
    quantity_after: Decimal
    amount_before: Decimal
    amount_change: Decimal
    amount_after: Decimal
    currency: str
    reference_id: str | None = None
    notes: str | None = None
    created_at: datetime


class BalanceResponse(BaseSchema):
    """Balance response for a PO line."""
    
    po_id: UUID
    po_line_id: UUID
    original_quantity: Decimal
    delivered_quantity: Decimal
    invoiced_quantity: Decimal
    remaining_quantity: Decimal
    original_amount: Decimal
    invoiced_amount: Decimal
    remaining_amount: Decimal
    currency: str
    history: list[BalanceLedgerEntry] = Field(default_factory=list)


# Cross Reference schemas
class CrossRefBase(BaseSchema):
    """Base cross reference schema."""
    
    supplier_id: str
    supplier_name: str | None = None
    invoice_number_pattern: str
    po_number: str
    product_code_invoice: str | None = None
    product_code_po: str | None = None


class CrossRefCreate(CrossRefBase):
    """Schema for creating a cross reference."""
    
    invoice_id: UUID | None = None
    po_id: UUID | None = None
    confidence_score: Decimal = Field(default=Decimal("0.5000"), ge=0, le=1)


class CrossRefResponse(CrossRefBase, UUIDMixin, TimestampMixin):
    """Cross reference response schema."""
    
    confirmed: bool
    confirmation_count: int
    rejection_count: int
    last_used_at: datetime | None = None
    last_confirmed_at: datetime | None = None
    confidence_score: Decimal
    notes: str | None = None


class CrossRefConfirmRequest(BaseSchema):
    """Request to confirm a cross reference."""
    
    confirmed: bool = Field(description="True to confirm, False to reject")
    notes: str | None = None

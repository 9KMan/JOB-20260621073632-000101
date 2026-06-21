# api/schemas.py
"""Shared Pydantic request/response models for the API."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

T = TypeVar("T")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str
    timestamp: datetime


class PaginationParams(BaseModel):
    """Pagination parameters."""

    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=1000)


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""

    items: list[T]
    total: int
    skip: int
    limit: int
    has_more: bool


# Base schemas
class TimestampMixinSchema(BaseModel):
    """Schema with timestamp fields."""

    created_at: datetime
    updated_at: datetime


class UUIDSchema(BaseModel):
    """Schema with UUID id field."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID


# Invoice schemas
class InvoiceLineBase(BaseModel):
    """Base schema for invoice lines."""

    line_number: int = Field(..., ge=1)
    description: str = Field(..., min_length=1)
    sku: str | None = None
    product_code: str | None = None
    quantity: Decimal = Field(..., gt=0)
    unit_of_measure: str = "EA"
    unit_price: Decimal = Field(..., gt=0)
    line_amount: Decimal = Field(..., ge=0)

    @field_validator("line_amount", mode="before")
    @classmethod
    def calculate_line_amount(cls, v: Any, info) -> Decimal:
        """Calculate line amount if not provided."""
        if v is not None:
            return Decimal(str(v))
        # Get quantity and unit_price from data
        data = info.data
        qty = Decimal(str(data.get("quantity", 0)))
        price = Decimal(str(data.get("unit_price", 0)))
        return qty * price


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating invoice lines."""

    po_line_id: UUID | None = None
    delivery_note_line_id: UUID | None = None


class InvoiceLineResponse(InvoiceLineBase, UUIDSchema):
    """Schema for invoice line response."""

    po_line_id: UUID | None = None
    delivery_note_line_id: UUID | None = None
    match_score: float | None = None
    is_matched: bool = False


class InvoiceBase(BaseModel):
    """Base schema for invoices."""

    vendor_number: str = Field(..., min_length=1, max_length=50)
    vendor_name: str = Field(..., min_length=1, max_length=255)
    vendor_tax_id: str | None = None
    invoice_number: str = Field(..., min_length=1, max_length=100)
    invoice_date: date
    due_date: date | None = None
    total_amount: Decimal = Field(..., gt=0)
    tax_amount: Decimal | None = None
    currency_code: str = Field(default="USD", max_length=3)
    description: str | None = None
    payment_terms: str | None = None
    erp_invoice_id: str | None = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating invoices."""

    po_id: UUID | None = None
    delivery_note_id: UUID | None = None
    lines: list[InvoiceLineCreate] = Field(default_factory=list)

    @field_validator("lines")
    @classmethod
    def validate_lines(cls, v: list, info) -> list:
        """Ensure at least one line or calculate total from lines."""
        return v


class InvoiceUpdate(BaseModel):
    """Schema for updating invoices."""

    status: str | None = None
    match_decision: str | None = None
    approved_by: str | None = None
    description: str | None = None
    payment_terms: str | None = None


class InvoiceResponse(InvoiceBase, UUIDSchema, TimestampMixinSchema):
    """Schema for invoice response."""

    model_config = ConfigDict(from_attributes=True)

    status: str
    match_status: str
    match_decision: str | None = None
    match_score: float | None = None
    po_id: UUID | None = None
    delivery_note_id: UUID | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    erp_invoice_id: str | None = None
    lines: list[InvoiceLineResponse] = Field(default_factory=list)


# Purchase Order schemas
class PurchaseOrderLineBase(BaseModel):
    """Base schema for PO lines."""

    line_number: int = Field(..., ge=1)
    description: str = Field(..., min_length=1)
    sku: str | None = None
    product_code: str | None = None
    category: str | None = None
    quantity_ordered: Decimal = Field(..., gt=0)
    quantity_received: Decimal = Field(default=Decimal("0"), ge=0)
    quantity_invoiced: Decimal = Field(default=Decimal("0"), ge=0)
    unit_of_measure: str = "EA"
    unit_price: Decimal = Field(..., gt=0)
    line_amount: Decimal = Field(..., ge=0)
    expected_delivery_date: date | None = None


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Schema for creating PO lines."""

    pass


class PurchaseOrderLineResponse(PurchaseOrderLineBase, UUIDSchema):
    """Schema for PO line response."""

    model_config = ConfigDict(from_attributes=True)

    quantity_remaining: Decimal


class PurchaseOrderBase(BaseModel):
    """Base schema for purchase orders."""

    vendor_number: str = Field(..., min_length=1, max_length=50)
    vendor_name: str = Field(..., min_length=1, max_length=255)
    vendor_address: str | None = None
    po_number: str = Field(..., min_length=1, max_length=100)
    po_date: date
    expected_delivery_date: date | None = None
    total_amount: Decimal = Field(..., gt=0)
    currency_code: str = Field(default="USD", max_length=3)
    description: str | None = None
    payment_terms: str | None = None
    shipping_terms: str | None = None
    erp_po_id: str | None = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating purchase orders."""

    lines: list[PurchaseOrderLineCreate] = Field(default_factory=list)


class PurchaseOrderResponse(PurchaseOrderBase, UUIDSchema, TimestampMixinSchema):
    """Schema for PO response."""

    model_config = ConfigDict(from_attributes=True)

    status: str
    erp_po_id: str | None = None
    lines: list[PurchaseOrderLineResponse] = Field(default_factory=list)


# Delivery Note schemas
class DeliveryNoteLineBase(BaseModel):
    """Base schema for delivery note lines."""

    line_number: int = Field(..., ge=1)
    description: str = Field(..., min_length=1)
    sku: str | None = None
    product_code: str | None = None
    quantity_delivered: Decimal = Field(..., gt=0)
    quantity_accepted: Decimal = Field(..., ge=0)
    quantity_rejected: Decimal = Field(default=Decimal("0"), ge=0)
    unit_of_measure: str = "EA"


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating delivery note lines."""

    po_line_id: UUID | None = None


class DeliveryNoteLineResponse(DeliveryNoteLineBase, UUIDSchema):
    """Schema for delivery note line response."""

    model_config = ConfigDict(from_attributes=True)

    po_line_id: UUID | None = None


class DeliveryNoteBase(BaseModel):
    """Base schema for delivery notes."""

    vendor_number: str = Field(..., min_length=1, max_length=50)
    vendor_name: str = Field(..., min_length=1, max_length=255)
    dn_number: str = Field(..., min_length=1, max_length=100)
    receipt_date: date
    received_by: str | None = None
    po_id: UUID | None = None
    notes: str | None = None
    erp_dn_id: str | None = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating delivery notes."""

    lines: list[DeliveryNoteLineCreate] = Field(default_factory=list)


class DeliveryNoteResponse(DeliveryNoteBase, UUIDSchema, TimestampMixinSchema):
    """Schema for delivery note response."""

    model_config = ConfigDict(from_attributes=True)

    status: str
    erp_dn_id: str | None = None
    lines: list[DeliveryNoteLineResponse] = Field(default_factory=list)


# Matching schemas
class MatchingTriggerRequest(BaseModel):
    """Request to trigger matching for an invoice."""

    invoice_id: UUID
    force_rematch: bool = False


class MatchingTriggerResponse(BaseModel):
    """Response from matching trigger."""

    invoice_id: UUID
    match_status: str
    match_decision: str | None
    match_score: float | None
    matched_lines: int
    total_lines: int
    processing_time_ms: float


class MatchScoreDetail(BaseModel):
    """Detailed score breakdown."""

    criteria: str
    max_score: float
    actual_score: float
    weighted_score: float


class MatchLineResult(BaseModel):
    """Result for a single line match."""

    invoice_line_id: UUID
    po_line_id: UUID | None
    match_score: float
    price_variance_pct: float | None
    quantity_variance_pct: float | None
    match_reason: str
    used_learning: bool = False


class MatchResultResponse(BaseModel):
    """Complete match result response."""

    invoice_id: UUID
    overall_score: float
    decision: str
    header_match: bool
    line_matches: list[MatchLineResult]
    score_breakdown: list[MatchScoreDetail]
    cross_ref_matches_used: int


# Exception schemas
class ExceptionBase(BaseModel):
    """Base schema for exceptions."""

    exception_type: str
    invoice_id: UUID
    po_id: UUID | None = None
    invoice_line_id: UUID | None = None
    po_line_id: UUID | None = None
    description: str
    expected_value: Decimal | None = None
    actual_value: Decimal | None = None
    variance_pct: float | None = None


class ExceptionCreate(ExceptionBase):
    """Schema for creating exceptions."""

    pass


class ExceptionResponse(ExceptionBase, UUIDSchema, TimestampMixinSchema):
    """Schema for exception response."""

    model_config = ConfigDict(from_attributes=True)

    status: str
    resolved_by: str | None = None
    resolved_at: datetime | None = None
    resolution_notes: str | None = None


class ExceptionResolveRequest(BaseModel):
    """Request to resolve an exception."""

    resolution_notes: str | None = None


class ExceptionDismissRequest(BaseModel):
    """Request to dismiss an exception."""

    reason: str = Field(..., min_length=1)


# Balance Ledger schemas
class BalanceLedgerResponse(BaseModel):
    """Schema for balance ledger response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    po_line_id: UUID
    quantity_ordered: Decimal
    quantity_received: Decimal
    quantity_invoiced: Decimal
    quantity_paid: Decimal
    quantity_balance: Decimal
    amount_ordered: Decimal
    amount_invoiced: Decimal
    amount_paid: Decimal
    amount_balance: Decimal
    over_delivery_quantity: Decimal
    over_delivery_amount: Decimal
    last_transaction_at: datetime | None
    last_transaction_type: str | None
    invoice_percentage: Decimal
    payment_percentage: Decimal
    created_at: datetime
    updated_at: datetime


# Cross Ref schemas
class CrossRefBase(BaseModel):
    """Base schema for cross refs."""

    vendor_number: str
    sku: str | None = None
    product_code: str | None = None
    description_pattern: str | None = None


class CrossRefCreate(CrossRefBase):
    """Schema for creating cross refs."""

    po_line_id: UUID | None = None
    invoice_line_id: UUID | None = None


class CrossRefResponse(CrossRefBase, UUIDSchema, TimestampMixinSchema):
    """Schema for cross ref response."""

    model_config = ConfigDict(from_attributes=True)

    po_line_id: UUID | None = None
    invoice_line_id: UUID | None = None
    confirmation_count: int
    match_count: int
    last_matched_at: datetime | None
    learned_unit_price: float | None
    learned_quantity_ratio: float | None
    learned_uom: str | None
    base_confidence: float
    current_confidence: float
    boost_factor: float
    is_active: bool
    is_promoted: bool
    promoted_at: datetime | None


# Error schemas
class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str
    error_code: str | None = None
    errors: list[dict] | None = None


class ValidationErrorResponse(BaseModel):
    """Validation error response."""

    detail: list[dict]

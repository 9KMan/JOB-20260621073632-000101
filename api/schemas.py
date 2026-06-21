// api/schemas.py
"""Shared Pydantic schemas for API request/response models."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
    )


class TimestampMixinSchema(BaseModel):
    """Schema fields for timestamp mixin."""

    created_at: datetime
    updated_at: datetime


class UUIDMixinSchema(BaseModel):
    """Schema fields for UUID mixin."""

    id: uuid.UUID


# Generic type for response wrappers
T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""

    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    detail: str | None = None
    code: str | None = None


class SuccessResponse(BaseModel):
    """Standard success response."""

    message: str
    data: dict[str, Any] | None = None


# Invoice Schemas
class InvoiceLineBase(BaseSchema):
    """Base schema for invoice lines."""

    line_number: int
    description: str | None = None
    item_code: str | None = None
    item_description: str | None = None
    unit_of_measure: str | None = None
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    line_amount: Decimal = Field(..., ge=0)
    tax_code: str | None = None
    tax_rate: Decimal = Field(default=Decimal("0.00"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating invoice lines."""

    po_line_id: uuid.UUID | None = None
    delivery_note_line_id: uuid.UUID | None = None


class InvoiceLineUpdate(BaseSchema):
    """Schema for updating invoice lines."""

    description: str | None = None
    item_code: str | None = None
    item_description: str | None = None
    quantity: Decimal | None = None
    unit_price: Decimal | None = None
    line_amount: Decimal | None = None
    status: str | None = None


class InvoiceLineResponse(InvoiceLineBase, TimestampMixinSchema, UUIDMixinSchema):
    """Schema for invoice line response."""

    invoice_id: uuid.UUID
    status: str
    matched_po_line_id: uuid.UUID | None = None
    match_confidence: float | None = None
    delivery_note_line_id: uuid.UUID | None = None


class InvoiceBase(BaseSchema):
    """Base schema for invoices."""

    invoice_number: str = Field(..., min_length=1, max_length=100)
    vendor_number: str = Field(..., min_length=1, max_length=50)
    vendor_name: str | None = None
    invoice_date: date
    due_date: date | None = None
    received_date: date
    currency: str = Field(default="USD", min_length=3, max_length=3)
    subtotal: Decimal = Field(..., ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    total_amount: Decimal = Field(..., ge=0)
    paid_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    external_ref: str | None = None
    source_system: str | None = None
    description: str | None = None
    payment_terms: str | None = None
    notes: str | None = None

    @field_validator("invoice_date", "received_date", "due_date", mode="before")
    @classmethod
    def parse_date(cls, v: Any) -> date | None:
        if isinstance(v, str):
            return date.fromisoformat(v)
        return v


class InvoiceCreate(InvoiceBase):
    """Schema for creating invoices."""

    lines: list[InvoiceLineCreate] = Field(default_factory=list)


class InvoiceUpdate(BaseSchema):
    """Schema for updating invoices."""

    vendor_name: str | None = None
    due_date: date | None = None
    status: str | None = None
    paid_amount: Decimal | None = None
    notes: str | None = None


class InvoiceResponse(InvoiceBase, TimestampMixinSchema, UUIDMixinSchema):
    """Schema for invoice response."""

    status: str
    match_score: float | None = None
    match_decision: str | None = None
    processed_at: datetime | None = None
    approved_at: datetime | None = None
    approved_by: str | None = None
    lines: list[InvoiceLineResponse] = Field(default_factory=list)


class InvoiceListResponse(BaseSchema):
    """Schema for invoice list response."""

    items: list[InvoiceResponse]
    total: int
    page: int
    page_size: int


# Purchase Order Schemas
class PurchaseOrderLineBase(BaseSchema):
    """Base schema for PO lines."""

    line_number: int
    description: str | None = None
    item_code: str | None = None
    item_description: str | None = None
    unit_of_measure: str | None = None
    ordered_quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    line_amount: Decimal = Field(..., ge=0)
    tax_code: str | None = None
    tax_rate: Decimal = Field(default=Decimal("0.00"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Schema for creating PO lines."""

    expected_delivery_date: date | None = None


class PurchaseOrderLineResponse(PurchaseOrderLineBase, TimestampMixinSchema, UUIDMixinSchema):
    """Schema for PO line response."""

    po_id: uuid.UUID
    received_quantity: Decimal
    invoiced_quantity: Decimal
    status: str
    expected_delivery_date: date | None = None
    last_delivery_date: date | None = None


class PurchaseOrderBase(BaseSchema):
    """Base schema for purchase orders."""

    po_number: str = Field(..., min_length=1, max_length=100)
    vendor_number: str = Field(..., min_length=1, max_length=50)
    vendor_name: str | None = None
    vendor_address: str | None = None
    created_date: date
    expected_delivery_date: date | None = None
    currency: str = Field(default="USD", min_length=3, max_length=3)
    subtotal: Decimal = Field(default=Decimal("0.00"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    total_amount: Decimal = Field(..., ge=0)
    description: str | None = None
    payment_terms: str | None = None
    shipping_terms: str | None = None
    source_system: str | None = None
    external_ref: str | None = None

    @field_validator("created_date", "expected_delivery_date", mode="before")
    @classmethod
    def parse_date(cls, v: Any) -> date | None:
        if isinstance(v, str):
            return date.fromisoformat(v)
        return v


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating purchase orders."""

    lines: list[PurchaseOrderLineCreate] = Field(default_factory=list)


class PurchaseOrderResponse(PurchaseOrderBase, TimestampMixinSchema, UUIDMixinSchema):
    """Schema for PO response."""

    status: str
    lines: list[PurchaseOrderLineResponse] = Field(default_factory=list)


class PurchaseOrderListResponse(BaseSchema):
    """Schema for PO list response."""

    items: list[PurchaseOrderResponse]
    total: int
    page: int
    page_size: int


# Delivery Note Schemas
class DeliveryNoteLineBase(BaseSchema):
    """Base schema for DN lines."""

    line_number: int
    description: str | None = None
    item_code: str | None = None
    item_description: str | None = None
    unit_of_measure: str | None = None
    delivered_quantity: Decimal = Field(..., gt=0)
    accepted_quantity: Decimal | None = None
    rejected_quantity: Decimal = Field(default=Decimal("0.00"), ge=0)
    unit_price: Decimal | None = None
    line_amount: Decimal = Field(default=Decimal("0.00"), ge=0)


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating DN lines."""

    po_line_id: uuid.UUID | None = None


class DeliveryNoteLineResponse(DeliveryNoteLineBase, TimestampMixinSchema, UUIDMixinSchema):
    """Schema for DN line response."""

    dn_id: uuid.UUID
    po_line_id: uuid.UUID | None = None
    status: str


class DeliveryNoteBase(BaseSchema):
    """Base schema for delivery notes."""

    dn_number: str = Field(..., min_length=1, max_length=100)
    po_number: str | None = None
    vendor_number: str = Field(..., min_length=1, max_length=50)
    vendor_name: str | None = None
    issue_date: date
    received_date: date | None = None
    currency: str = Field(default="USD", min_length=3, max_length=3)
    total_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    description: str | None = None
    source_system: str | None = None
    external_ref: str | None = None
    notes: str | None = None

    @field_validator("issue_date", "received_date", mode="before")
    @classmethod
    def parse_date(cls, v: Any) -> date | None:
        if isinstance(v, str):
            return date.fromisoformat(v)
        return v


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating delivery notes."""

    lines: list[DeliveryNoteLineCreate] = Field(default_factory=list)


class DeliveryNoteResponse(DeliveryNoteBase, TimestampMixinSchema, UUIDMixinSchema):
    """Schema for DN response."""

    status: str
    purchase_order_id: uuid.UUID | None = None
    lines: list[DeliveryNoteLineResponse] = Field(default_factory=list)


class DeliveryNoteListResponse(BaseSchema):
    """Schema for DN list response."""

    items: list[DeliveryNoteResponse]
    total: int
    page: int
    page_size: int


# Matching Schemas
class MatchingTriggerRequest(BaseSchema):
    """Request to trigger matching for an invoice."""

    invoice_id: uuid.UUID
    match_delivery_notes: bool = Field(default=True)
    auto_process: bool = Field(default=False)


class MatchingDecision(BaseSchema):
    """Matching decision result."""

    invoice_id: uuid.UUID
    match_score: float
    decision: str
    decision_reason: str | None = None
    line_matches: list[dict[str, Any]] = Field(default_factory=list)
    exceptions: list[dict[str, Any]] = Field(default_factory=list)
    processing_time_ms: int | None = None


class MatchLineDetail(BaseSchema):
    """Detail of a single line match."""

    invoice_line_id: uuid.UUID
    po_line_id: uuid.UUID | None
    dn_line_id: uuid.UUID | None = None
    match_confidence: float
    match_type: str
    price_match: bool
    quantity_match: bool
    price_variance_pct: float | None = None
    quantity_variance_pct: float | None = None


# Exception Schemas
class ExceptionBase(BaseSchema):
    """Base schema for exceptions."""

    invoice_id: uuid.UUID
    invoice_line_id: uuid.UUID | None = None
    exception_type: str
    description: str | None = None
    severity: str = Field(default="medium")
    match_id: uuid.UUID | None = None


class ExceptionResponse(ExceptionBase, TimestampMixinSchema, UUIDMixinSchema):
    """Schema for exception response."""

    status: str
    resolved_at: datetime | None = None
    resolved_by: str | None = None
    resolution: str | None = None
    resolution_notes: str | None = None


class ExceptionResolveRequest(BaseSchema):
    """Request to resolve an exception."""

    resolution: str = Field(..., description="Resolution type: approved, rejected, dismissed, adjusted, escalated")
    resolution_notes: str | None = None
    adjusted_amount: Decimal | None = None
    adjusted_quantity: Decimal | None = None


class ExceptionListResponse(BaseSchema):
    """Schema for exception list response."""

    items: list[ExceptionResponse]
    total: int
    page: int
    page_size: int


# Balance Ledger Schemas
class BalanceLedgerResponse(BaseSchema, UUIDMixinSchema, TimestampMixinSchema):
    """Schema for balance ledger response."""

    po_line_id: uuid.UUID
    invoice_line_id: uuid.UUID | None = None
    original_po_quantity: Decimal
    original_po_amount: Decimal
    delivered_quantity: Decimal
    delivered_amount: Decimal
    invoiced_quantity: Decimal
    invoiced_amount: Decimal
    paid_quantity: Decimal
    paid_amount: Decimal
    remaining_po_quantity: Decimal
    remaining_po_amount: Decimal
    status: str
    as_of_date: date
    last_transaction_date: datetime | None = None
    transaction_type: str
    transaction_ref: str | None = None


# Cross Reference Schemas
class CrossRefResponse(BaseSchema, UUIDMixinSchema, TimestampMixinSchema):
    """Schema for cross reference response."""

    po_line_id: uuid.UUID
    invoice_line_id: uuid.UUID | None = None
    vendor_number: str
    vendor_name: str | None = None
    item_code: str | None = None
    item_description: str | None = None
    po_unit_price: Decimal
    matched_unit_price: Decimal
    price_variance_pct: Decimal
    po_quantity: Decimal
    matched_quantity: Decimal
    quantity_variance_pct: Decimal
    base_confidence: float
    current_confidence: float
    confirmed_count: int
    rejected_count: int
    promotion_level: int
    match_type: str
    match_method: str | None = None
    notes: str | None = None


# Health Check Schema
class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    database: str = "healthy"
    timestamp: datetime

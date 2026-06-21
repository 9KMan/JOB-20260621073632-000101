# api/schemas.py
"""Shared Pydantic schemas for API request/response models."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    model_config = ConfigDict(from_attributes=True)

    error: str
    detail: str | None = None
    code: str | None = None


class HealthResponse(BaseModel):
    """Health check response schema."""

    model_config = ConfigDict(from_attributes=True)

    status: str = "healthy"
    version: str
    timestamp: datetime


class PaginationMeta(BaseModel):
    """Pagination metadata."""

    total: int
    page: int
    page_size: int
    total_pages: int


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    model_config = ConfigDict(from_attributes=True)

    data: list[T]
    pagination: PaginationMeta


# Base schemas for common fields
class MoneyFields(BaseModel):
    """Mixin for money/amount fields."""

    gross_amount: Decimal
    tax_amount: Decimal = Field(default=Decimal("0.00"))
    net_amount: Decimal
    currency: str = Field(default="USD", max_length=3)


class DateFields(BaseModel):
    """Mixin for date fields."""

    invoice_date: date | None = None
    due_date: date | None = None
    po_date: date | None = None
    delivery_date: date | None = None
    dn_date: date | None = None
    receipt_date: date | None = None


# Invoice schemas
class InvoiceLineBase(BaseModel):
    """Base schema for invoice line."""

    model_config = ConfigDict(from_attributes=True)

    line_number: int
    description: str = Field(max_length=500)
    quantity: Decimal = Field(ge=0)
    unit_of_measure: str = Field(default="EA", max_length=10)
    unit_price: Decimal = Field(ge=0)
    gross_amount: Decimal = Field(ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"))
    net_amount: Decimal
    part_number: str | None = Field(default=None, max_length=100)


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating invoice line."""

    po_line_id: UUID | None = None
    delivery_line_id: UUID | None = None


class InvoiceLineResponse(InvoiceLineBase):
    """Schema for invoice line response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    invoice_id: UUID
    matched: bool
    match_score: float | None = None


class InvoiceBase(BaseModel):
    """Base schema for invoice."""

    model_config = ConfigDict(from_attributes=True)

    invoice_number: str = Field(max_length=50)
    vendor_id: str = Field(max_length=50)
    vendor_name: str = Field(max_length=255)
    invoice_date: date
    due_date: date | None = None
    gross_amount: Decimal = Field(ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"))
    net_amount: Decimal
    currency: str = Field(default="USD", max_length=3)
    payment_terms: str | None = Field(default=None, max_length=100)
    notes: str | None = None
    is_credit_memo: bool = False
    source_system: str | None = Field(default=None, max_length=50)
    external_ref: str | None = Field(default=None, max_length=100)


class InvoiceCreate(InvoiceBase):
    """Schema for creating invoice."""

    lines: list[InvoiceLineCreate] = Field(default_factory=list)


class InvoiceUpdate(BaseModel):
    """Schema for updating invoice."""

    status: str | None = None
    due_date: date | None = None
    payment_terms: str | None = None
    notes: str | None = None


class InvoiceResponse(InvoiceBase):
    """Schema for invoice response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    invoice_type: str
    created_at: datetime
    updated_at: datetime
    matched_at: datetime | None = None
    approved_at: datetime | None = None
    lines: list[InvoiceLineResponse] = Field(default_factory=list)


# Purchase Order schemas
class POLineBase(BaseModel):
    """Base schema for PO line."""

    model_config = ConfigDict(from_attributes=True)

    line_number: int
    description: str = Field(max_length=500)
    part_number: str | None = Field(default=None, max_length=100)
    quantity: Decimal = Field(ge=0)
    unit_of_measure: str = Field(default="EA", max_length=10)
    unit_price: Decimal = Field(ge=0)
    gross_amount: Decimal = Field(ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"))
    net_amount: Decimal
    schedule_date: date | None = None
    promised_date: date | None = None


class POLineCreate(POLineBase):
    """Schema for creating PO line."""

    pass


class POLineResponse(POLineBase):
    """Schema for PO line response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    po_id: UUID
    received_quantity: Decimal
    invoiced_quantity: Decimal


class PurchaseOrderBase(BaseModel):
    """Base schema for purchase order."""

    model_config = ConfigDict(from_attributes=True)

    po_number: str = Field(max_length=50)
    vendor_id: str = Field(max_length=50)
    vendor_name: str = Field(max_length=255)
    po_date: date
    delivery_date: date | None = None
    gross_amount: Decimal = Field(ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"))
    net_amount: Decimal
    currency: str = Field(default="USD", max_length=3)
    payment_terms: str | None = Field(default=None, max_length=100)
    ship_to: str | None = Field(default=None, max_length=255)
    notes: str | None = None
    is_blanket: bool = False
    blanket_po_id: UUID | None = None
    source_system: str | None = Field(default=None, max_length=50)
    external_ref: str | None = Field(default=None, max_length=100)


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating purchase order."""

    lines: list[POLineCreate] = Field(default_factory=list)


class PurchaseOrderResponse(PurchaseOrderBase):
    """Schema for purchase order response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    po_type: str
    created_at: datetime
    updated_at: datetime
    lines: list[POLineResponse] = Field(default_factory=list)


# Delivery Note schemas
class DeliveryNoteLineBase(BaseModel):
    """Base schema for delivery note line."""

    model_config = ConfigDict(from_attributes=True)

    line_number: int
    description: str = Field(max_length=500)
    part_number: str | None = Field(default=None, max_length=100)
    quantity: Decimal = Field(ge=0)
    unit_of_measure: str = Field(default="EA", max_length=10)
    unit_price: Decimal | None = None
    net_amount: Decimal
    po_line_id: UUID | None = None


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating delivery note line."""

    pass


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """Schema for delivery note line response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dn_id: UUID
    invoiced_quantity: Decimal
    received: bool


class DeliveryNoteBase(BaseModel):
    """Base schema for delivery note."""

    model_config = ConfigDict(from_attributes=True)

    dn_number: str = Field(max_length=50)
    vendor_id: str = Field(max_length=50)
    vendor_name: str = Field(max_length=255)
    po_number: str | None = Field(default=None, max_length=50)
    po_id: UUID | None = None
    dn_date: date
    receipt_date: date | None = None
    gross_amount: Decimal = Field(ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"))
    net_amount: Decimal
    currency: str = Field(default="USD", max_length=3)
    notes: str | None = None
    carrier: str | None = Field(default=None, max_length=100)
    tracking_number: str | None = Field(default=None, max_length=100)
    source_system: str | None = Field(default=None, max_length=50)
    external_ref: str | None = Field(default=None, max_length=100)


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating delivery note."""

    lines: list[DeliveryNoteLineCreate] = Field(default_factory=list)


class DeliveryNoteResponse(DeliveryNoteBase):
    """Schema for delivery note response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    lines: list[DeliveryNoteLineResponse] = Field(default_factory=list)


# Matching schemas
class MatchingResult(BaseModel):
    """Schema for matching result per line."""

    invoice_line_id: UUID
    po_line_id: UUID | None
    match_score: float
    decision: str
    match_type: str | None = None


class MatchingResponse(BaseModel):
    """Schema for matching response."""

    model_config = ConfigDict(from_attributes=True)

    invoice_id: UUID
    status: str
    total_lines: int
    matched_lines: int
    match_score: float
    decision: str
    results: list[MatchingResult]
    processed_at: datetime


# Exception schemas
class ExceptionBase(BaseModel):
    """Base schema for exception."""

    model_config = ConfigDict(from_attributes=True)

    exception_type: str
    invoice_id: UUID
    invoice_line_id: UUID | None = None
    po_line_id: UUID | None = None
    description: str
    severity: str = "medium"


class ExceptionCreate(ExceptionBase):
    """Schema for creating exception."""

    pass


class ExceptionResponse(ExceptionBase):
    """Schema for exception response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    resolved_at: datetime | None = None
    resolved_by: UUID | None = None
    resolution_notes: str | None = None
    created_at: datetime
    updated_at: datetime


# Balance ledger schemas
class BalanceLedgerEntry(BaseModel):
    """Schema for balance ledger entry."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    po_line_id: UUID
    transaction_type: str
    quantity_before: Decimal
    quantity_change: Decimal
    quantity_after: Decimal
    amount_before: Decimal
    amount_change: Decimal
    amount_after: Decimal
    currency: str
    reference: str | None
    transaction_date: datetime
    created_at: datetime


class POLineBalance(BaseModel):
    """Schema for PO line balance summary."""

    model_config = ConfigDict(from_attributes=True)

    po_line_id: UUID
    po_number: str
    line_number: int
    ordered_quantity: Decimal
    received_quantity: Decimal
    invoiced_quantity: Decimal
    pending_quantity: Decimal
    pending_amount: Decimal
    currency: str

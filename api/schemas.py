# api/schemas.py
"""Shared Pydantic schemas for API request/response models."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BaseSchema(BaseModel):
    """Base Pydantic schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
    )


class PaginationParams(BaseSchema):
    """Pagination parameters."""

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")


class PaginatedResponse(BaseSchema, Generic[T]):
    """Paginated response wrapper."""

    items: list[T]
    total: int = Field(ge=0)
    page: int
    page_size: int
    total_pages: int

    @field_validator("total_pages", mode="before")
    @classmethod
    def calculate_total_pages(cls, v: int, info: Any) -> int:
        """Calculate total pages from total and page_size."""
        if v == 0:
            return 0
        return v


# Invoice Schemas
class InvoiceLineBase(BaseSchema):
    """Base schema for invoice line."""

    line_number: int
    description: str = Field(max_length=500)
    product_number: str | None = None
    product_description: str | None = None
    quantity: Decimal = Field(ge=0)
    unit_price: Decimal = Field(ge=0)
    line_amount: Decimal = Field(ge=0)
    tax_code: str | None = None
    tax_rate: Decimal = Field(default=Decimal("0"))


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating an invoice line."""

    po_line_id: uuid.UUID | None = None


class InvoiceLineResponse(InvoiceLineBase):
    """Schema for invoice line response."""

    id: uuid.UUID
    invoice_id: uuid.UUID
    quantity_invoiced: Decimal
    status: str
    po_line_id: uuid.UUID | None = None
    matched_quantity: Decimal
    match_score: float | None = None
    created_at: datetime
    updated_at: datetime


class InvoiceBase(BaseSchema):
    """Base schema for invoice."""

    invoice_number: str = Field(max_length=50)
    vendor_number: str = Field(max_length=50)
    vendor_name: str | None = None
    po_number: str | None = None
    invoice_date: date
    due_date: date | None = None
    subtotal: Decimal = Field(ge=0)
    tax_amount: Decimal = Field(ge=0)
    total_amount: Decimal = Field(ge=0)
    currency_code: str = Field(default="USD", max_length=3)
    source_system: str | None = None
    source_id: str | None = None
    notes: str | None = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating an invoice."""

    lines: list[InvoiceLineCreate] = Field(default_factory=list)


class InvoiceUpdate(BaseSchema):
    """Schema for updating an invoice."""

    vendor_name: str | None = None
    due_date: date | None = None
    notes: str | None = None
    status: str | None = None


class InvoiceResponse(InvoiceBase):
    """Schema for invoice response."""

    id: uuid.UUID
    po_id: uuid.UUID | None = None
    status: str
    match_score: float | None = None
    match_decision: str | None = None
    matched_at: datetime | None = None
    has_exceptions: bool
    exception_count: int
    approved_by: str | None = None
    approved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    lines: list[InvoiceLineResponse] = Field(default_factory=list)


class InvoiceListResponse(BaseSchema):
    """Schema for invoice list item."""

    id: uuid.UUID
    invoice_number: str
    vendor_number: str
    vendor_name: str | None = None
    invoice_date: date
    total_amount: Decimal
    currency_code: str
    status: str
    match_score: float | None = None
    has_exceptions: bool
    created_at: datetime


# Purchase Order Schemas
class POLineBase(BaseSchema):
    """Base schema for PO line."""

    line_number: int
    description: str = Field(max_length=500)
    product_number: str | None = None
    product_description: str | None = None
    quantity_ordered: Decimal = Field(ge=0)
    unit_price: Decimal = Field(ge=0)
    line_amount: Decimal = Field(ge=0)
    tax_code: str | None = None
    tax_rate: Decimal = Field(default=Decimal("0"))


class POLineCreate(POLineBase):
    """Schema for creating a PO line."""


class POLineResponse(POLineBase):
    """Schema for PO line response."""

    id: uuid.UUID
    po_id: uuid.UUID
    quantity_received: Decimal
    quantity_invoiced: Decimal
    status: str
    created_at: datetime
    updated_at: datetime


class PurchaseOrderBase(BaseSchema):
    """Base schema for purchase order."""

    po_number: str = Field(max_length=50)
    vendor_number: str = Field(max_length=50)
    vendor_name: str | None = None
    issue_date: date
    expected_date: date | None = None
    expiration_date: date | None = None
    subtotal: Decimal = Field(ge=0)
    tax_amount: Decimal = Field(ge=0)
    total_amount: Decimal = Field(ge=0)
    currency_code: str = Field(default="USD", max_length=3)
    source_system: str | None = None
    source_id: str | None = None
    notes: str | None = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a purchase order."""

    lines: list[POLineCreate] = Field(default_factory=list)


class PurchaseOrderResponse(PurchaseOrderBase):
    """Schema for purchase order response."""

    id: uuid.UUID
    status: str
    total_lines: int
    total_quantity: Decimal
    received_quantity: Decimal
    created_at: datetime
    updated_at: datetime
    lines: list[POLineResponse] = Field(default_factory=list)


class PurchaseOrderListResponse(BaseSchema):
    """Schema for purchase order list item."""

    id: uuid.UUID
    po_number: str
    vendor_number: str
    vendor_name: str | None = None
    issue_date: date
    total_amount: Decimal
    currency_code: str
    status: str
    receipt_percentage: float
    created_at: datetime


# Delivery Note Schemas
class DNLineBase(BaseSchema):
    """Base schema for delivery note line."""

    line_number: int
    description: str = Field(max_length=500)
    product_number: str | None = None
    product_description: str | None = None
    quantity_delivered: Decimal = Field(ge=0)
    unit_price: Decimal = Field(ge=0)
    line_amount: Decimal = Field(ge=0)


class DNLineCreate(DNLineBase):
    """Schema for creating a delivery note line."""

    po_line_id: uuid.UUID | None = None


class DNLineResponse(DNLineBase):
    """Schema for delivery note line response."""

    id: uuid.UUID
    dn_id: uuid.UUID
    quantity_received: Decimal
    status: str
    po_line_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime


class DeliveryNoteBase(BaseSchema):
    """Base schema for delivery note."""

    dn_number: str = Field(max_length=50)
    vendor_number: str = Field(max_length=50)
    vendor_name: str | None = None
    po_number: str | None = None
    delivery_date: date
    received_date: date | None = None
    total_amount: Decimal = Field(ge=0)
    currency_code: str = Field(default="USD", max_length=3)
    source_system: str | None = None
    source_id: str | None = None
    notes: str | None = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating a delivery note."""

    lines: list[DNLineCreate] = Field(default_factory=list)


class DeliveryNoteResponse(DeliveryNoteBase):
    """Schema for delivery note response."""

    id: uuid.UUID
    po_id: uuid.UUID | None = None
    status: str
    is_fully_invoiced: bool
    invoiced_amount: Decimal
    created_at: datetime
    updated_at: datetime
    lines: list[DNLineResponse] = Field(default_factory=list)


class DeliveryNoteListResponse(BaseSchema):
    """Schema for delivery note list item."""

    id: uuid.UUID
    dn_number: str
    vendor_number: str
    vendor_name: str | None = None
    po_number: str | None = None
    delivery_date: date
    total_amount: Decimal
    currency_code: str
    status: str
    is_fully_invoiced: bool
    created_at: datetime


# Matching Schemas
class MatchingRequest(BaseSchema):
    """Schema for triggering invoice matching."""

    invoice_id: uuid.UUID
    po_id: uuid.UUID | None = None


class MatchingResultLine(BaseSchema):
    """Schema for matching result on a single line."""

    invoice_line_id: uuid.UUID
    po_line_id: uuid.UUID | None = None
    dn_line_ids: list[uuid.UUID] = Field(default_factory=list)
    matched_quantity: Decimal
    matched_amount: Decimal
    price_variance: Decimal
    qty_variance: Decimal
    score: float
    exceptions: list[str] = Field(default_factory=list)


class MatchingResult(BaseSchema):
    """Schema for matching result."""

    invoice_id: uuid.UUID
    po_id: uuid.UUID | None = None
    overall_score: float
    decision: str
    lines: list[MatchingResultLine]
    total_matched_amount: Decimal
    total_variance: Decimal
    exceptions: list[dict[str, Any]] = Field(default_factory=list)
    matched_at: datetime


# Exception Schemas
class ExceptionResponse(BaseSchema):
    """Schema for exception response."""

    id: uuid.UUID
    invoice_id: uuid.UUID
    exception_type: str
    severity: str
    description: str
    field_name: str | None = None
    expected_value: str | None = None
    actual_value: str | None = None
    resolution: str | None = None
    resolved_by: str | None = None
    resolved_at: datetime | None = None
    created_at: datetime


class ExceptionResolveRequest(BaseSchema):
    """Schema for resolving an exception."""

    resolution: str
    notes: str | None = None
    adjusted_value: Decimal | None = None


class ExceptionDismissRequest(BaseSchema):
    """Schema for dismissing an exception."""

    reason: str


# Balance Ledger Schemas
class BalanceLedgerResponse(BaseSchema):
    """Schema for balance ledger response."""

    id: uuid.UUID
    document_type: str
    document_number: str
    vendor_number: str
    vendor_name: str | None = None
    original_amount: Decimal
    open_amount: Decimal
    paid_amount: Decimal
    original_quantity: Decimal
    open_quantity: Decimal
    paid_quantity: Decimal
    document_date: date
    due_date: date | None = None
    status: str
    paid_date: date | None = None
    payment_reference: str | None = None
    po_line_id: uuid.UUID | None = None
    invoice_line_id: uuid.UUID | None = None
    created_at: datetime


# Cross-Reference Schemas
class CrossRefResponse(BaseSchema):
    """Schema for cross-reference response."""

    id: uuid.UUID
    ref_type: str
    vendor_number: str
    vendor_name: str | None = None
    product_number: str | None = None
    product_description: str | None = None
    po_number: str | None = None
    po_line_number: int | None = None
    unit_price: Decimal | None = None
    quantity: Decimal | None = None
    tax_code: str | None = None
    confirmed_count: int
    rejected_count: int
    confidence_score: float
    status: str
    is_promoted: bool
    valid_from: date
    valid_until: date | None = None
    created_at: datetime


# Generic Response Schemas
class SuccessResponse(BaseSchema):
    """Generic success response."""

    success: bool = True
    message: str
    data: dict[str, Any] | None = None


class ErrorResponse(BaseSchema):
    """Generic error response."""

    success: bool = False
    error: str
    detail: str | None = None
    code: str | None = None


# Token Schemas
class Token(BaseSchema):
    """Token response schema."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseSchema):
    """Token payload data."""

    sub: str
    exp: datetime
    type: str = "access"

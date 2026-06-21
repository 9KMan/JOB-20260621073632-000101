# api/schemas.py
"""Shared Pydantic request/response models."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BaseResponse(BaseModel):
    """Base response model."""

    model_config = ConfigDict(from_attributes=True)


class PaginationMeta(BaseModel):
    """Pagination metadata."""

    total: int
    page: int
    per_page: int
    pages: int


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""

    data: list[T]
    meta: PaginationMeta


class InvoiceLineSchema(BaseModel):
    """Invoice line item schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID | None = None
    line_number: int
    description: str
    product_code: str | None = None
    product_name: str | None = None
    quantity: Decimal
    unit_of_measure: str | None = None
    unit_price: Decimal
    line_amount: Decimal
    tax_rate: Decimal | None = None
    tax_amount: Decimal | None = None
    status: str = "pending"
    matched_po_line_id: uuid.UUID | None = None
    price_match_score: float | None = None
    qty_match_score: float | None = None
    overall_match_score: float | None = None
    has_exception: bool = False
    exception_reason: str | None = None


class InvoiceCreateSchema(BaseModel):
    """Schema for creating an invoice."""

    vendor_id: str = Field(..., min_length=1, max_length=100)
    vendor_name: str = Field(..., min_length=1, max_length=255)
    vendor_tax_id: str | None = None
    invoice_number: str = Field(..., min_length=1, max_length=100)
    invoice_date: date
    due_date: date | None = None
    posting_date: date | None = None
    currency: str = Field(default="USD", max_length=3)
    total_amount: Decimal
    tax_amount: Decimal | None = None
    net_amount: Decimal | None = None
    notes: str | None = None
    lines: list[InvoiceLineSchema] = Field(..., min_length=1)

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency code."""
        return v.upper()


class InvoiceResponseSchema(BaseModel):
    """Schema for invoice response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    vendor_id: str
    vendor_name: str
    invoice_number: str
    invoice_date: date
    due_date: date | None
    currency: str
    total_amount: Decimal
    tax_amount: Decimal | None
    status: str
    match_decision: str | None
    match_score: float | None
    has_exception: bool
    exception_type: str | None
    exception_reason: str | None
    created_at: datetime
    updated_at: datetime
    lines: list[InvoiceLineSchema] = []


class InvoiceListResponse(BaseModel):
    """Schema for invoice list response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    vendor_id: str
    vendor_name: str
    invoice_number: str
    invoice_date: date
    total_amount: Decimal
    currency: str
    status: str
    match_decision: str | None
    has_exception: bool


class PurchaseOrderLineSchema(BaseModel):
    """Purchase order line item schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID | None = None
    line_number: int
    description: str
    product_code: str | None = None
    product_name: str | None = None
    quantity: Decimal
    unit_of_measure: str | None = None
    unit_price: Decimal
    line_amount: Decimal
    received_quantity: Decimal = Decimal("0")
    invoiced_quantity: Decimal = Decimal("0")
    status: str = "pending"


class PurchaseOrderCreateSchema(BaseModel):
    """Schema for creating a purchase order."""

    vendor_id: str = Field(..., min_length=1, max_length=100)
    vendor_name: str = Field(..., min_length=1, max_length=255)
    vendor_address: str | None = None
    po_number: str = Field(..., min_length=1, max_length=100)
    po_date: date
    delivery_date: date | None = None
    currency: str = Field(default="USD", max_length=3)
    total_amount: Decimal
    tax_amount: Decimal | None = None
    notes: str | None = None
    lines: list[PurchaseOrderLineSchema] = Field(..., min_length=1)


class PurchaseOrderResponseSchema(BaseModel):
    """Schema for purchase order response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    vendor_id: str
    vendor_name: str
    po_number: str
    po_date: date
    delivery_date: date | None
    currency: str
    total_amount: Decimal
    status: str
    created_at: datetime
    updated_at: datetime
    lines: list[PurchaseOrderLineSchema] = []


class PurchaseOrderListResponse(BaseModel):
    """Schema for purchase order list response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    vendor_id: str
    vendor_name: str
    po_number: str
    po_date: date
    total_amount: Decimal
    currency: str
    status: str


class DeliveryNoteLineSchema(BaseModel):
    """Delivery note line item schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID | None = None
    line_number: int
    description: str
    product_code: str | None = None
    product_name: str | None = None
    quantity: Decimal
    unit_of_measure: str | None = None
    po_line_id: uuid.UUID | None = None


class DeliveryNoteCreateSchema(BaseModel):
    """Schema for creating a delivery note."""

    vendor_id: str = Field(..., min_length=1, max_length=100)
    vendor_name: str = Field(..., min_length=1, max_length=255)
    dn_number: str = Field(..., min_length=1, max_length=100)
    dn_date: date
    receipt_date: date | None = None
    purchase_order_id: uuid.UUID | None = None
    notes: str | None = None
    lines: list[DeliveryNoteLineSchema] = Field(..., min_length=1)


class DeliveryNoteResponseSchema(BaseModel):
    """Schema for delivery note response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    vendor_id: str
    vendor_name: str
    dn_number: str
    dn_date: date
    receipt_date: date | None
    purchase_order_id: uuid.UUID | None
    status: str
    created_at: datetime
    updated_at: datetime
    lines: list[DeliveryNoteLineSchema] = []


class MatchingTriggerSchema(BaseModel):
    """Schema for triggering matching."""

    invoice_id: uuid.UUID


class MatchingDecisionSchema(BaseModel):
    """Schema for matching decision."""

    model_config = ConfigDict(from_attributes=True)

    invoice_id: uuid.UUID
    decision: str
    score: float
    matched_po_id: uuid.UUID | None
    matched_dn_id: uuid.UUID | None
    matched_lines: list[dict[str, Any]] = []
    exceptions: list[dict[str, Any]] = []


class ExceptionResponseSchema(BaseModel):
    """Schema for exception response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    invoice_id: uuid.UUID
    invoice_number: str
    exception_type: str
    exception_reason: str | None
    status: str
    created_at: datetime
    resolved_by: str | None
    resolved_at: datetime | None


class ExceptionResolveSchema(BaseModel):
    """Schema for resolving an exception."""

    resolution: str = Field(..., min_length=1)
    notes: str | None = None


class ExceptionDismissSchema(BaseModel):
    """Schema for dismissing an exception."""

    reason: str = Field(..., min_length=1)
    notes: str | None = None


class BalanceLedgerResponseSchema(BaseModel):
    """Schema for balance ledger response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    po_line_id: uuid.UUID
    purchase_order_id: uuid.UUID
    vendor_id: str
    original_quantity: Decimal
    received_quantity: Decimal
    invoiced_quantity: Decimal
    open_quantity: Decimal
    open_amount: Decimal
    unit_price: Decimal
    currency: str
    status: str


class ErrorResponse(BaseModel):
    """Schema for error responses."""

    detail: str
    code: str | None = None
    extra: dict[str, Any] | None = None


class SuccessResponse(BaseModel):
    """Schema for success responses."""

    message: str
    data: dict[str, Any] | None = None

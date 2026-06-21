# api/schemas.py
"""Shared Pydantic schemas for API request/response validation."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator


T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    """Base response wrapper for all API responses."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_serialization_defaults_required=True,
    )

    success: bool = True
    data: T | None = None
    message: str | None = None
    error: str | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_serialization_defaults_required=True,
    )

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


class ErrorResponse(BaseModel):
    """Standard error response."""

    model_config = ConfigDict(
        json_schema_serialization_defaults_required=True,
    )

    success: bool = False
    error: str
    detail: str | None = None
    code: str | None = None


class InvoiceLineItemCreate(BaseModel):
    """Schema for creating an invoice line item."""

    line_number: int = Field(..., ge=1)
    description: str = Field(..., min_length=1, max_length=500)
    quantity: Decimal = Field(..., gt=0, decimal_places=4)
    unit_of_measure: str | None = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=0, decimal_places=4)
    tax_rate: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=4)
    po_line_reference: str | None = Field(default=None, max_length=100)


class InvoiceLineItemResponse(BaseModel):
    """Schema for invoice line item response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    line_number: int
    description: str
    quantity: Decimal
    unit_of_measure: str | None
    unit_price: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    amount: Decimal
    po_line_reference: str | None
    is_matched: bool
    match_confidence: float | None


class InvoiceCreate(BaseModel):
    """Schema for creating an invoice."""

    invoice_number: str = Field(..., min_length=1, max_length=100)
    supplier_id: str = Field(..., min_length=1, max_length=100)
    supplier_name: str = Field(..., min_length=1, max_length=255)
    supplier_tax_id: str | None = Field(default=None, max_length=50)
    invoice_date: date
    due_date: date | None = None
    subtotal: Decimal = Field(default=Decimal("0"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0"), ge=0)
    total_amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    notes: str | None = None
    line_items: list[InvoiceLineItemCreate] = Field(..., min_length=1)
    metadata: dict | None = None

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        return v.upper()


class InvoiceUpdate(BaseModel):
    """Schema for updating an invoice."""

    supplier_id: str | None = None
    supplier_name: str | None = None
    due_date: date | None = None
    status: str | None = None
    notes: str | None = None
    metadata: dict | None = None


class InvoiceResponse(BaseModel):
    """Schema for invoice response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    invoice_number: str
    supplier_id: str
    supplier_name: str
    supplier_tax_id: str | None
    invoice_date: date
    due_date: date | None
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    currency: str
    matching_decision: str | None
    match_score: float | None
    matched_at: datetime | None
    approved_at: datetime | None
    paid_amount: Decimal
    line_items: list[InvoiceLineItemResponse]
    created_at: datetime
    updated_at: datetime


class PurchaseOrderLineItemCreate(BaseModel):
    """Schema for creating a PO line item."""

    line_number: int = Field(..., ge=1)
    description: str = Field(..., min_length=1, max_length=500)
    quantity: Decimal = Field(..., gt=0, decimal_places=4)
    unit_of_measure: str | None = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=0, decimal_places=4)
    tax_rate: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=4)


class PurchaseOrderLineItemResponse(BaseModel):
    """Schema for PO line item response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    line_number: int
    description: str
    quantity: Decimal
    unit_of_measure: str | None
    unit_price: Decimal
    tax_rate: Decimal
    amount: Decimal
    quantity_received: Decimal
    quantity_invoiced: Decimal


class PurchaseOrderCreate(BaseModel):
    """Schema for creating a purchase order."""

    po_number: str = Field(..., min_length=1, max_length=100)
    supplier_id: str = Field(..., min_length=1, max_length=100)
    supplier_name: str = Field(..., min_length=1, max_length=255)
    supplier_tax_id: str | None = Field(default=None, max_length=50)
    order_date: date
    delivery_date: date | None = None
    subtotal: Decimal = Field(default=Decimal("0"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0"), ge=0)
    total_amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    notes: str | None = None
    line_items: list[PurchaseOrderLineItemCreate] = Field(..., min_length=1)
    metadata: dict | None = None

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        return v.upper()


class PurchaseOrderResponse(BaseModel):
    """Schema for purchase order response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    po_number: str
    supplier_id: str
    supplier_name: str
    supplier_tax_id: str | None
    order_date: date
    delivery_date: date | None
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    currency: str
    line_items: list[PurchaseOrderLineItemResponse]
    created_at: datetime
    updated_at: datetime


class DeliveryNoteLineItemCreate(BaseModel):
    """Schema for creating a delivery note line item."""

    line_number: int = Field(..., ge=1)
    description: str = Field(..., min_length=1, max_length=500)
    quantity: Decimal = Field(..., gt=0, decimal_places=4)
    unit_of_measure: str | None = Field(default="EA", max_length=20)
    po_line_reference: str | None = None


class DeliveryNoteCreate(BaseModel):
    """Schema for creating a delivery note."""

    dn_number: str = Field(..., min_length=1, max_length=100)
    supplier_id: str = Field(..., min_length=1, max_length=100)
    supplier_name: str = Field(..., min_length=1, max_length=255)
    po_reference: str | None = Field(default=None, max_length=100)
    delivery_date: date
    notes: str | None = None
    line_items: list[DeliveryNoteLineItemCreate] = Field(..., min_length=1)
    metadata: dict | None = None


class DeliveryNoteResponse(BaseModel):
    """Schema for delivery note response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    dn_number: str
    supplier_id: str
    supplier_name: str
    po_reference: str | None
    delivery_date: date
    status: str
    line_items: list
    created_at: datetime
    updated_at: datetime


class MatchingTriggerRequest(BaseModel):
    """Schema for triggering matching."""

    invoice_id: uuid.UUID
    auto_process: bool = True


class MatchingDecisionResponse(BaseModel):
    """Schema for matching decision response."""

    model_config = ConfigDict(from_attributes=True)

    invoice_id: uuid.UUID
    decision: str
    score: float
    threshold_used: str
    match_count: int
    exceptions: list[dict[str, Any]]


class ExceptionCreate(BaseModel):
    """Schema for creating an exception."""

    exception_type: str
    invoice_id: uuid.UUID
    po_line_item_id: uuid.UUID | None = None
    cross_ref_id: uuid.UUID | None = None
    description: str
    amount_variance: Decimal | None = None
    quantity_variance: Decimal | None = None
    notes: str | None = None


class ExceptionResponse(BaseModel):
    """Schema for exception response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    exception_type: str
    invoice_id: uuid.UUID
    po_line_item_id: uuid.UUID | None
    cross_ref_id: uuid.UUID | None
    description: str
    amount_variance: Decimal | None
    quantity_variance: Decimal | None
    status: str
    notes: str | None
    created_at: datetime
    resolved_at: datetime | None
    resolved_by: str | None


class BalanceLedgerResponse(BaseModel):
    """Schema for balance ledger response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    po_line_item_id: uuid.UUID
    original_quantity: Decimal
    quantity_delivered: Decimal
    quantity_invoiced: Decimal
    quantity_credited: Decimal
    quantity_open: Decimal
    original_amount: Decimal
    amount_delivered: Decimal
    amount_invoiced: Decimal
    amount_credited: Decimal
    amount_open: Decimal
    last_delivery_date: date | None
    last_invoice_date: date | None
    status: str


class CrossRefResponse(BaseModel):
    """Schema for cross reference response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    invoice_line_item_id: uuid.UUID
    po_line_item_id: uuid.UUID
    match_status: str
    match_confidence: float
    confidence_level: str
    match_decision: str
    is_auto_matched: bool
    price_match: bool
    quantity_match: bool
    supplier_match: bool
    price_variance: Decimal
    quantity_variance: Decimal
    confirmed_at: datetime | None
    is_promoted: bool
    created_at: datetime


class HealthCheckResponse(BaseModel):
    """Schema for health check response."""

    status: str
    version: str
    database: str
    timestamp: datetime

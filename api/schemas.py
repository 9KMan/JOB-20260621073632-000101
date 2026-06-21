# api/schemas.py
"""Shared Pydantic schemas for request/response models."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )


# Generic type for paginated responses
T = TypeVar("T")


class PaginatedResponse(BaseSchema, Generic[T]):
    """Paginated response wrapper."""

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        """Create a paginated response.

        Args:
            items: List of items for current page
            total: Total number of items
            page: Current page number
            page_size: Items per page

        Returns:
            PaginatedResponse: Paginated response instance
        """
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


class ErrorResponse(BaseSchema):
    """Standard error response."""

    detail: str
    code: str | None = None
    errors: list[dict[str, Any]] | None = None


class SuccessResponse(BaseSchema):
    """Standard success response."""

    message: str
    data: dict[str, Any] | None = None


# Invoice Schemas
class InvoiceLineBase(BaseSchema):
    """Base invoice line schema."""

    line_number: str
    line_type: str = "ITEM"
    product_code: str | None = None
    product_name: str | None = None
    description: str | None = None
    quantity: Decimal = Field(default=Decimal("0.0000"))
    unit_price: Decimal = Field(default=Decimal("0.0000"))
    price: Decimal = Field(default=Decimal("0.00"))
    tax_rate: Decimal = Field(default=Decimal("0.0000"))
    tax_amount: Decimal = Field(default=Decimal("0.00"))
    line_total: Decimal = Field(default=Decimal("0.00"))


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating an invoice line."""

    matched_po_line_id: uuid.UUID | None = None
    match_score: float | None = None


class InvoiceLineResponse(InvoiceLineBase):
    """Schema for invoice line response."""

    id: uuid.UUID
    invoice_id: uuid.UUID
    quantity_received: Decimal
    quantity_invoiced: Decimal
    matched_po_line_id: uuid.UUID | None = None
    match_score: float | None = None
    created_at: datetime
    updated_at: datetime


class InvoiceBase(BaseSchema):
    """Base invoice schema."""

    invoice_number: str
    vendor_id: str
    vendor_name: str | None = None
    invoice_date: date
    due_date: date | None = None
    currency: str = "USD"
    subtotal: Decimal = Field(default=Decimal("0.00"))
    tax_amount: Decimal = Field(default=Decimal("0.00"))
    total_amount: Decimal
    description: str | None = None
    notes: str | None = None
    metadata_json: dict[str, Any] | None = None
    erp_reference: str | None = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating an invoice."""

    lines: list[InvoiceLineCreate] = Field(default_factory=list)
    matched_po_id: uuid.UUID | None = None


class InvoiceUpdate(BaseSchema):
    """Schema for updating an invoice."""

    status: str | None = None
    notes: str | None = None
    metadata_json: dict[str, Any] | None = None


class InvoiceResponse(InvoiceBase):
    """Schema for invoice response."""

    id: uuid.UUID
    status: str
    matched_po_id: uuid.UUID | None = None
    match_score: float | None = None
    match_decision: str | None = None
    match_confidence: str | None = None
    match_decision_at: datetime | None = None
    paid: bool
    paid_at: datetime | None = None
    payment_reference: str | None = None
    lines: list[InvoiceLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class InvoiceListResponse(BaseSchema):
    """Schema for invoice list item (without lines)."""

    id: uuid.UUID
    invoice_number: str
    vendor_id: str
    vendor_name: str | None = None
    invoice_date: date
    total_amount: Decimal
    currency: str
    status: str
    match_score: float | None = None
    match_decision: str | None = None
    paid: bool
    created_at: datetime


# Purchase Order Schemas
class PurchaseOrderLineBase(BaseSchema):
    """Base PO line schema."""

    line_number: str
    line_type: str = "ITEM"
    product_code: str | None = None
    product_name: str | None = None
    description: str | None = None
    manufacturer_code: str | None = None
    quantity_ordered: Decimal
    unit_price: Decimal = Field(default=Decimal("0.0000"))
    price: Decimal = Field(default=Decimal("0.00"))
    tax_rate: Decimal = Field(default=Decimal("0.0000"))
    tax_amount: Decimal = Field(default=Decimal("0.00"))
    line_total: Decimal = Field(default=Decimal("0.00"))
    promised_delivery_date: date | None = None


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Schema for creating a PO line."""

    pass


class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    """Schema for PO line response."""

    id: uuid.UUID
    po_id: uuid.UUID
    quantity_received: Decimal
    quantity_invoiced: Decimal
    quantity_shipped: Decimal
    is_fully_received: bool
    is_fully_invoiced: bool
    is_fully_paid: bool
    created_at: datetime
    updated_at: datetime


class PurchaseOrderBase(BaseSchema):
    """Base PO schema."""

    po_number: str
    vendor_id: str
    vendor_name: str | None = None
    po_date: date
    delivery_date: date | None = None
    expiration_date: date | None = None
    currency: str = "USD"
    subtotal: Decimal = Field(default=Decimal("0.00"))
    tax_amount: Decimal = Field(default=Decimal("0.00"))
    total_amount: Decimal
    payment_terms: str | None = None
    payment_method: str | None = None
    ship_to: str | None = None
    ship_from: str | None = None
    description: str | None = None
    notes: str | None = None
    metadata_json: dict[str, Any] | None = None
    erp_reference: str | None = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a PO."""

    lines: list[PurchaseOrderLineCreate] = Field(default_factory=list)


class PurchaseOrderResponse(PurchaseOrderBase):
    """Schema for PO response."""

    id: uuid.UUID
    status: str
    closed_at: datetime | None = None
    closed_by: str | None = None
    lines: list[PurchaseOrderLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class PurchaseOrderListResponse(BaseSchema):
    """Schema for PO list item (without lines)."""

    id: uuid.UUID
    po_number: str
    vendor_id: str
    vendor_name: str | None = None
    po_date: date
    total_amount: Decimal
    currency: str
    status: str
    created_at: datetime


# Delivery Note Schemas
class DeliveryNoteLineBase(BaseSchema):
    """Base DN line schema."""

    line_number: str
    product_code: str | None = None
    product_name: str | None = None
    description: str | None = None
    quantity_shipped: Decimal
    quantity_received: Decimal = Field(default=Decimal("0.0000"))
    quantity_returned: Decimal = Field(default=Decimal("0.0000"))
    unit_price: Decimal | None = None
    line_total: Decimal | None = None


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating a DN line."""

    po_line_id: uuid.UUID | None = None


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """Schema for DN line response."""

    id: uuid.UUID
    dn_id: uuid.UUID
    po_line_id: uuid.UUID | None = None
    is_received: bool
    is_fully_matched: bool
    match_score: float | None = None
    created_at: datetime
    updated_at: datetime


class DeliveryNoteBase(BaseSchema):
    """Base delivery note schema."""

    dn_number: str
    vendor_id: str
    vendor_name: str | None = None
    po_id: uuid.UUID | None = None
    po_number: str | None = None
    dn_date: date
    expected_delivery_date: date | None = None
    actual_delivery_date: date | None = None
    status: str = "ISSUED"
    ship_from: str | None = None
    ship_to: str | None = None
    tracking_number: str | None = None
    carrier: str | None = None
    currency: str = "USD"
    description: str | None = None
    notes: str | None = None
    metadata_json: dict[str, Any] | None = None
    erp_reference: str | None = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating a delivery note."""

    lines: list[DeliveryNoteLineCreate] = Field(default_factory=list)


class DeliveryNoteResponse(DeliveryNoteBase):
    """Schema for delivery note response."""

    id: uuid.UUID
    lines: list[DeliveryNoteLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class DeliveryNoteListResponse(BaseSchema):
    """Schema for DN list item (without lines)."""

    id: uuid.UUID
    dn_number: str
    vendor_id: str
    vendor_name: str | None = None
    po_number: str | None = None
    dn_date: date
    status: str
    created_at: datetime


# Matching Schemas
class MatchTriggerRequest(BaseSchema):
    """Request to trigger matching for an invoice."""

    invoice_id: uuid.UUID
    force_rematch: bool = False


class MatchDecisionResponse(BaseSchema):
    """Response containing match decision."""

    invoice_id: uuid.UUID
    decision: str
    match_score: float
    confidence: str
    matched_po_id: uuid.UUID | None = None
    matched_lines: list[dict[str, Any]] = Field(default_factory=list)
    exceptions: list[dict[str, Any]] = Field(default_factory=list)
    processing_time_ms: int


class MatchScoreDetail(BaseSchema):
    """Detailed score breakdown for a match."""

    criteria: str
    score: float
    max_score: float
    weight: float
    details: str | None = None


# Exception Schemas
class ExceptionBase(BaseSchema):
    """Base exception schema."""

    exception_type: str
    invoice_id: uuid.UUID
    po_id: uuid.UUID | None = None
    description: str


class ExceptionResponse(ExceptionBase):
    """Schema for exception response."""

    id: uuid.UUID
    status: str
    resolved_by: str | None = None
    resolved_at: datetime | None = None
    resolution_notes: str | None = None
    created_at: datetime
    updated_at: datetime


class ExceptionResolveRequest(BaseSchema):
    """Request to resolve an exception."""

    resolution_notes: str | None = None


class ExceptionDismissRequest(BaseSchema):
    """Request to dismiss an exception."""

    dismissal_reason: str


# Balance Ledger Schemas
class BalanceLedgerResponse(BaseSchema):
    """Schema for balance ledger entry response."""

    id: uuid.UUID
    po_line_id: uuid.UUID
    invoice_line_id: uuid.UUID | None = None
    transaction_type: str
    reference_id: str
    reference_type: str
    quantity_before: Decimal
    quantity_change: Decimal
    quantity_after: Decimal
    value_before: Decimal
    value_change: Decimal
    value_after: Decimal
    unit_price: Decimal
    balance_type: str
    transaction_date: datetime
    created_by: str | None = None
    notes: str | None = None
    created_at: datetime


class BalanceSummaryResponse(BaseSchema):
    """Schema for balance summary for a PO line."""

    po_line_id: uuid.UUID
    product_code: str | None = None
    quantity_ordered: Decimal
    quantity_received: Decimal
    quantity_invoiced: Decimal
    quantity_remaining: Decimal
    value_ordered: Decimal
    value_received: Decimal
    value_invoiced: Decimal
    value_remaining: Decimal


# Cross Ref Schemas
class CrossRefResponse(BaseSchema):
    """Schema for cross reference response."""

    id: uuid.UUID
    po_vendor_id: str
    po_vendor_name: str | None = None
    po_product_code: str | None = None
    po_product_name: str | None = None
    invoice_vendor_id: str
    invoice_vendor_name: str | None = None
    invoice_product_code: str | None = None
    invoice_product_name: str | None = None
    matched_unit_price: Decimal | None = None
    matched_quantity: Decimal | None = None
    match_count: int
    average_match_score: float
    last_match_score: float | None = None
    last_matched_at: datetime | None = None
    confidence: str
    learning_status: str
    is_active: bool
    is_manually_verified: bool
    created_at: datetime
    updated_at: datetime


class CrossRefCreate(BaseSchema):
    """Schema for manually creating a cross reference."""

    po_vendor_id: str
    po_vendor_name: str | None = None
    po_product_code: str | None = None
    po_product_name: str | None = None
    invoice_vendor_id: str
    invoice_vendor_name: str | None = None
    invoice_product_code: str | None = None
    invoice_product_name: str | None = None
    price_tolerance_percent: float | None = None
    qty_tolerance_percent: float | None = None
    notes: str | None = None


# Filter Schemas
class InvoiceFilter(BaseSchema):
    """Filter parameters for invoice listing."""

    vendor_id: str | None = None
    status: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    min_amount: Decimal | None = None
    max_amount: Decimal | None = None
    matched: bool | None = None
    paid: bool | None = None


class PurchaseOrderFilter(BaseSchema):
    """Filter parameters for PO listing."""

    vendor_id: str | None = None
    status: str | None = None
    date_from: date | None = None
    date_to: date | None = None


class DeliveryNoteFilter(BaseSchema):
    """Filter parameters for DN listing."""

    vendor_id: str | None = None
    po_id: uuid.UUID | None = None
    status: str | None = None
    date_from: date | None = None
    date_to: date | None = None


class ExceptionFilter(BaseSchema):
    """Filter parameters for exception listing."""

    status: str | None = None
    exception_type: str | None = None
    invoice_id: uuid.UUID | None = None
    date_from: date | None = None
    date_to: date | None = None

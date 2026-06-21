# api/schemas.py
"""Shared Pydantic schemas for API request/response models."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from models.enums import (
    DeliveryNoteStatus,
    ExceptionResolution,
    ExceptionType,
    InvoiceStatus,
    LineStatus,
    MatchingDecision,
    PurchaseOrderStatus,
)


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        validate_assignment=True,
    )


class TimestampMixin(BaseSchema):
    """Mixin schema for timestamp fields."""

    created_at: datetime
    updated_at: datetime


class UUIDMixin(BaseSchema):
    """Mixin schema for UUID id field."""

    id: str


class LineItemBase(BaseSchema):
    """Base schema for line items across all document types."""

    line_number: int = Field(..., ge=1)
    description: str = Field(..., min_length=1, max_length=500)
    quantity: Annotated[Decimal, Field(..., ge=0)]
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Annotated[Decimal, Field(..., ge=0)]
    line_amount: Annotated[Decimal, Field(..., ge=0)]
    tax_code: str | None = Field(default=None, max_length=20)
    status: LineStatus = Field(default=LineStatus.OPEN)


class InvoiceLineCreate(LineItemBase):
    """Schema for creating an invoice line."""

    po_line_id: str | None = None
    delivery_line_id: str | None = None


class InvoiceLineResponse(LineItemBase, UUIDMixin, TimestampMixin):
    """Schema for invoice line response."""

    invoice_id: str
    po_line_id: str | None = None
    delivery_line_id: str | None = None
    match_score: float | None = None


class InvoiceBase(BaseSchema):
    """Base schema for invoice data."""

    vendor_number: str = Field(..., min_length=1, max_length=50)
    vendor_name: str = Field(..., min_length=1, max_length=255)
    invoice_number: str = Field(..., min_length=1, max_length=100)
    invoice_date: date
    due_date: date | None = None
    total_amount: Annotated[Decimal, Field(..., ge=0)]
    currency_code: str = Field(default="USD", max_length=3)
    notes: str | None = Field(default=None, max_length=2000)
    source_system: str = Field(default="manual", max_length=50)
    external_reference: str | None = Field(default=None, max_length=255)
    tax_amount: Annotated[Decimal, Field(default=Decimal("0.00"), ge=0)]
    is_credit_memo: bool = Field(default=False)


class InvoiceCreate(InvoiceBase):
    """Schema for creating an invoice."""

    lines: list[InvoiceLineCreate] = Field(..., min_length=1)

    @field_validator("lines")
    @classmethod
    def validate_lines(cls, v: list) -> list:
        """Validate that line numbers are unique and sequential."""
        line_numbers = [line.line_number for line in v]
        if len(line_numbers) != len(set(line_numbers)):
            raise ValueError("Line numbers must be unique")
        if sorted(line_numbers) != list(range(1, len(line_numbers) + 1)):
            raise ValueError("Line numbers must be sequential starting from 1")
        return v


class InvoiceUpdate(BaseSchema):
    """Schema for updating an invoice."""

    vendor_number: str | None = Field(default=None, max_length=50)
    vendor_name: str | None = Field(default=None, max_length=255)
    due_date: date | None = None
    total_amount: Annotated[Decimal, Field(default=None, ge=0)]
    currency_code: str | None = Field(default=None, max_length=3)
    notes: str | None = Field(default=None, max_length=2000)
    status: InvoiceStatus | None = None


class InvoiceResponse(InvoiceBase, UUIDMixin, TimestampMixin):
    """Schema for invoice response."""

    status: InvoiceStatus
    is_deleted: bool
    deleted_at: datetime | None = None
    lines: list[InvoiceLineResponse] = Field(default_factory=list)


class InvoiceListResponse(BaseSchema):
    """Schema for paginated invoice list response."""

    items: list[InvoiceResponse]
    total: int
    page: int
    page_size: int
    pages: int


class POLineBase(LineItemBase):
    """Base schema for PO line data."""

    item_number: str = Field(..., min_length=1, max_length=50)
    delivery_date: date | None = None


class POLineCreate(POLineBase):
    """Schema for creating a PO line."""

    pass


class POLineResponse(POLineBase, UUIDMixin, TimestampMixin):
    """Schema for PO line response."""

    po_id: str
    status: LineStatus


class PurchaseOrderBase(BaseSchema):
    """Base schema for purchase order data."""

    vendor_number: str = Field(..., min_length=1, max_length=50)
    vendor_name: str = Field(..., min_length=1, max_length=255)
    po_number: str = Field(..., min_length=1, max_length=100)
    po_date: date
    delivery_date: date | None = None
    total_amount: Annotated[Decimal, Field(..., ge=0)]
    currency_code: str = Field(default="USD", max_length=3)
    notes: str | None = Field(default=None, max_length=2000)
    source_system: str = Field(default="erp", max_length=50)
    department_code: str | None = Field(default=None, max_length=50)
    cost_center: str | None = Field(default=None, max_length=50)


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a purchase order."""

    lines: list[POLineCreate] = Field(..., min_length=1)


class PurchaseOrderResponse(PurchaseOrderBase, UUIDMixin, TimestampMixin):
    """Schema for purchase order response."""

    status: PurchaseOrderStatus
    is_deleted: bool
    deleted_at: datetime | None = None
    lines: list[POLineResponse] = Field(default_factory=list)


class PurchaseOrderListResponse(BaseSchema):
    """Schema for paginated PO list response."""

    items: list[PurchaseOrderResponse]
    total: int
    page: int
    page_size: int
    pages: int


class DeliveryNoteLineBase(LineItemBase):
    """Base schema for delivery note line data."""

    item_number: str = Field(..., min_length=1, max_length=50)


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating a delivery note line."""

    po_line_id: str | None = None


class DeliveryNoteLineResponse(DeliveryNoteLineBase, UUIDMixin, TimestampMixin):
    """Schema for delivery note line response."""

    dn_id: str
    po_line_id: str | None = None
    status: LineStatus


class DeliveryNoteBase(BaseSchema):
    """Base schema for delivery note data."""

    vendor_number: str = Field(..., min_length=1, max_length=50)
    vendor_name: str = Field(..., min_length=1, max_length=255)
    dn_number: str = Field(..., min_length=1, max_length=100)
    receipt_date: date
    po_number: str | None = Field(default=None, max_length=100)
    total_amount: Annotated[Decimal, Field(..., ge=0)]
    currency_code: str = Field(default="USD", max_length=3)
    notes: str | None = Field(default=None, max_length=2000)
    source_system: str = Field(default="erp", max_length=50)
    received_by: str | None = Field(default=None, max_length=100)
    warehouse_location: str | None = Field(default=None, max_length=100)


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating a delivery note."""

    lines: list[DeliveryNoteLineCreate] = Field(..., min_length=1)


class DeliveryNoteResponse(DeliveryNoteBase, UUIDMixin, TimestampMixin):
    """Schema for delivery note response."""

    status: DeliveryNoteStatus
    is_deleted: bool
    deleted_at: datetime | None = None
    lines: list[DeliveryNoteLineResponse] = Field(default_factory=list)


class DeliveryNoteListResponse(BaseSchema):
    """Schema for paginated delivery note list response."""

    items: list[DeliveryNoteResponse]
    total: int
    page: int
    page_size: int
    pages: int


class MatchingTriggerRequest(BaseSchema):
    """Schema for triggering matching on an invoice."""

    invoice_id: str
    force_rematch: bool = Field(default=False)


class MatchingDecisionResponse(BaseSchema):
    """Schema for matching decision response."""

    invoice_id: str
    invoice_number: str
    decision: MatchingDecision
    overall_score: float
    lines_processed: int
    lines_matched: int
    lines_exception: int
    exception_ids: list[str] = Field(default_factory=list)
    matched_at: datetime


class LineMatchDetail(BaseSchema):
    """Schema for individual line match details."""

    invoice_line_id: str
    line_number: int
    description: str
    invoice_quantity: Decimal
    invoice_unit_price: Decimal
    matched_po_line_id: str | None
    matched_po_number: str | None
    matched_delivery_line_id: str | None
    matched_dn_number: str | None
    matched_quantity: Decimal | None
    matched_unit_price: Decimal | None
    quantity_variance: Decimal | None
    price_variance: Decimal | None
    match_score: float
    match_type: str


class ExceptionResponse(BaseSchema):
    """Schema for matching exception response."""

    id: str
    invoice_id: str
    invoice_number: str
    invoice_line_id: str | None
    line_number: int | None
    exception_type: ExceptionType
    description: str
    decision: MatchingDecision
    match_score: float | None
    notes: str | None
    resolution: ExceptionResolution | None
    resolved_at: datetime | None
    resolved_by: str | None
    created_at: datetime


class ExceptionListResponse(BaseSchema):
    """Schema for paginated exception list response."""

    items: list[ExceptionResponse]
    total: int
    page: int
    page_size: int
    pages: int


class ExceptionResolveRequest(BaseSchema):
    """Schema for resolving an exception."""

    resolution: ExceptionResolution
    notes: str | None = Field(default=None, max_length=2000)
    adjusted_amount: Decimal | None = Field(default=None)


class ExceptionDismissRequest(BaseSchema):
    """Schema for dismissing an exception."""

    reason: str = Field(..., min_length=1, max_length=500)


class BalanceLedgerResponse(BaseSchema):
    """Schema for balance ledger entry response."""

    id: str
    po_line_id: str | None
    delivery_line_id: str | None
    invoice_line_id: str | None
    balance_type: str
    transaction_date: date
    quantity: Decimal
    amount: Decimal
    unit_price: Decimal | None
    source_type: str
    source_id: str
    reference_number: str | None
    notes: str | None
    created_at: datetime


class CrossRefResponse(BaseSchema):
    """Schema for cross-reference response."""

    id: str
    invoice_line_id: str | None
    po_line_id: str | None
    delivery_line_id: str | None
    vendor_number: str
    item_number: str
    match_date: date
    decision: MatchingDecision
    match_score: float
    price_match_score: float | None
    qty_match_score: float | None
    confirmed: bool
    confirmed_at: date | None
    confirmed_by: str | None
    promotion_count: int
    created_at: datetime


class HealthResponse(BaseSchema):
    """Schema for health check response."""

    status: str
    version: str
    database: str
    timestamp: datetime


class ErrorResponse(BaseSchema):
    """Schema for error responses."""

    detail: str
    error_code: str | None = None
    field_errors: dict[str, list[str]] | None = None

# api/schemas.py
"""Shared Pydantic request/response models."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from models.enums import (
    DeliveryNoteStatus,
    ExceptionReason,
    ExceptionStatus,
    InvoiceStatus,
    MatchConfidence,
    MatchDecision,
    MatchStatus,
    PurchaseOrderStatus,
)


# Generic response wrapper
T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""

    success: bool = True
    data: T | None = None
    message: str | None = None
    error: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""

    success: bool = True
    data: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class ErrorResponse(BaseModel):
    """Error response model."""

    success: bool = False
    error: str
    detail: str | None = None
    code: str | None = None


# Invoice Schemas
class InvoiceLineBase(BaseModel):
    """Base schema for invoice line items."""

    line_number: str
    description: str
    quantity: Decimal
    unit_of_measure: str | None = None
    unit_price: Decimal
    line_amount: Decimal
    tax_rate: Decimal | None = None
    tax_amount: Decimal | None = None
    purchase_order_line_id: UUID | None = None


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating an invoice line."""

    pass


class InvoiceLineResponse(InvoiceLineBase):
    """Schema for invoice line response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    matched_quantity: Decimal = Decimal("0")
    matched_amount: Decimal = Decimal("0")
    match_score: float | None = None


class InvoiceBase(BaseModel):
    """Base schema for invoices."""

    vendor_number: str
    vendor_name: str
    invoice_number: str
    invoice_date: date
    due_date: date | None = None
    subtotal: Decimal
    tax_amount: Decimal = Decimal("0")
    total_amount: Decimal
    currency: str = "USD"
    purchase_order_number: str | None = None
    delivery_note_number: str | None = None
    payment_terms: str | None = None
    description: str | None = None
    raw_data: dict[str, Any] | None = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating an invoice."""

    lines: list[InvoiceLineCreate]


class InvoiceUpdate(BaseModel):
    """Schema for updating an invoice."""

    status: InvoiceStatus | None = None
    match_status: MatchStatus | None = None
    approved_by: str | None = None
    rejection_reason: str | None = None
    description: str | None = None


class InvoiceResponse(InvoiceBase):
    """Schema for invoice response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: InvoiceStatus
    match_status: MatchStatus
    match_score: float | None = None
    match_decision: str | None = None
    matched_at: datetime | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    rejection_reason: str | None = None
    created_at: datetime
    updated_at: datetime
    lines: list[InvoiceLineResponse] = []


class InvoiceListResponse(BaseModel):
    """Schema for invoice list response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vendor_number: str
    vendor_name: str
    invoice_number: str
    invoice_date: date
    total_amount: Decimal
    currency: str
    status: InvoiceStatus
    match_status: MatchStatus
    match_score: float | None = None
    match_decision: str | None = None


# Purchase Order Schemas
class PurchaseOrderLineBase(BaseModel):
    """Base schema for PO lines."""

    line_number: str
    item_number: str | None = None
    description: str
    ordered_quantity: Decimal
    unit_of_measure: str | None = None
    unit_price: Decimal
    line_amount: Decimal
    tax_rate: Decimal | None = None
    tax_amount: Decimal | None = None


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Schema for creating a PO line."""

    pass


class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    """Schema for PO line response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    received_quantity: Decimal = Decimal("0")
    invoiced_quantity: Decimal = Decimal("0")
    remaining_quantity: Decimal
    remaining_amount: Decimal
    is_closed: bool = False


class PurchaseOrderBase(BaseModel):
    """Base schema for purchase orders."""

    vendor_number: str
    vendor_name: str
    po_number: str
    order_date: date
    expected_delivery_date: date | None = None
    subtotal: Decimal
    tax_amount: Decimal = Decimal("0")
    total_amount: Decimal
    currency: str = "USD"
    payment_terms: str | None = None
    shipping_terms: str | None = None
    description: str | None = None
    erp_id: str | None = None
    raw_data: dict[str, Any] | None = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a PO."""

    lines: list[PurchaseOrderLineCreate]


class PurchaseOrderResponse(PurchaseOrderBase):
    """Schema for PO response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: PurchaseOrderStatus
    created_at: datetime
    updated_at: datetime
    lines: list[PurchaseOrderLineResponse] = []


class PurchaseOrderListResponse(BaseModel):
    """Schema for PO list response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vendor_number: str
    vendor_name: str
    po_number: str
    order_date: date
    total_amount: Decimal
    currency: str
    status: PurchaseOrderStatus


# Delivery Note Schemas
class DeliveryNoteLineBase(BaseModel):
    """Base schema for DN lines."""

    line_number: str
    item_number: str | None = None
    description: str
    quantity: Decimal
    unit_of_measure: str | None = None
    purchase_order_line_id: UUID | None = None


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating a DN line."""

    pass


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """Schema for DN line response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_invoiced: bool = False
    invoiced_quantity: Decimal = Decimal("0")


class DeliveryNoteBase(BaseModel):
    """Base schema for delivery notes."""

    vendor_number: str
    vendor_name: str
    dn_number: str
    receipt_date: date
    purchase_order_id: UUID | None = None
    purchase_order_number: str | None = None
    received_by: str | None = None
    location: str | None = None
    notes: str | None = None
    erp_id: str | None = None
    raw_data: dict[str, Any] | None = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating a DN."""

    lines: list[DeliveryNoteLineCreate]


class DeliveryNoteResponse(DeliveryNoteBase):
    """Schema for DN response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: DeliveryNoteStatus
    created_at: datetime
    updated_at: datetime
    lines: list[DeliveryNoteLineResponse] = []


class DeliveryNoteListResponse(BaseModel):
    """Schema for DN list response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vendor_number: str
    vendor_name: str
    dn_number: str
    receipt_date: date
    status: DeliveryNoteStatus


# Matching Schemas
class MatchRequest(BaseModel):
    """Schema for triggering a match."""

    invoice_id: UUID
    purchase_order_id: UUID | None = None
    force_rematch: bool = False


class MatchResultLine(BaseModel):
    """Schema for a single line match result."""

    invoice_line_id: UUID
    purchase_order_line_id: UUID | None = None
    price_match_score: float
    quantity_match_score: float
    date_match_score: float | None = None
    item_match_score: float | None = None
    overall_score: float
    match_decision: MatchDecision
    match_confidence: MatchConfidence
    exception_reason: ExceptionReason | None = None


class MatchResult(BaseModel):
    """Schema for complete match result."""

    invoice_id: UUID
    overall_score: float
    decision: MatchDecision
    confidence: MatchConfidence
    matched_lines: list[MatchResultLine]
    unmatched_lines: list[UUID]
    exceptions: list[dict[str, Any]] = []


class MatchDecisionRequest(BaseModel):
    """Schema for approving/rejecting a match."""

    invoice_id: UUID
    decision: MatchDecision
    approved_lines: list[UUID] = []
    rejected_lines: list[UUID] = []
    override_reason: str | None = None


# Exception Schemas
class ExceptionBase(BaseModel):
    """Base schema for exceptions."""

    reason: ExceptionReason
    invoice_id: UUID
    purchase_order_id: UUID | None = None
    invoice_line_id: UUID | None = None
    purchase_order_line_id: UUID | None = None
    expected_value: Decimal | None = None
    actual_value: Decimal | None = None
    variance: Decimal | None = None
    notes: str | None = None


class ExceptionCreate(ExceptionBase):
    """Schema for creating an exception."""

    pass


class ExceptionResponse(ExceptionBase):
    """Schema for exception response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: ExceptionStatus
    created_at: datetime
    updated_at: datetime
    resolved_by: str | None = None
    resolved_at: datetime | None = None
    resolution_notes: str | None = None


class ExceptionResolveRequest(BaseModel):
    """Schema for resolving an exception."""

    exception_id: UUID
    resolution: str
    adjust_values: bool = False


class ExceptionDismissRequest(BaseModel):
    """Schema for dismissing an exception."""

    exception_id: UUID
    reason: str


# Balance Ledger Schemas
class BalanceLedgerResponse(BaseModel):
    """Schema for balance ledger response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    purchase_order_line_id: UUID
    reference_type: str
    reference_id: UUID
    reference_number: str
    transaction_date: date
    transaction_type: str
    quantity_change: Decimal
    amount_change: Decimal
    running_quantity: Decimal
    running_amount: Decimal
    match_status: MatchStatus
    match_score: float | None = None
    match_decision: str | None = None


class BalanceSummary(BaseModel):
    """Schema for balance summary per PO line."""

    purchase_order_line_id: UUID
    po_number: str
    line_number: str
    description: str
    original_quantity: Decimal
    original_amount: Decimal
    open_quantity: Decimal
    open_amount: Decimal
    match_status: str


# Cross Reference Schemas
class CrossRefResponse(BaseModel):
    """Schema for cross-reference response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vendor_number: str
    supplier_item_number: str | None = None
    our_item_number: str | None = None
    item_description: str | None = None
    standard_price: Decimal | None = None
    standard_quantity: Decimal | None = None
    match_score: float
    match_confidence: MatchConfidence
    times_matched: int
    times_confirmed: int
    times_rejected: int
    confirmation_rate: float
    is_active: bool


# Auth Schemas
class Token(BaseModel):
    """JWT Token response."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data."""

    sub: str
    exp: datetime
    iat: datetime


class LoginRequest(BaseModel):
    """Login request."""

    username: str
    password: str

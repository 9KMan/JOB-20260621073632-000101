// app/api/schemas.py
"""Shared Pydantic schemas for request/response models."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator


T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Get limit for database query."""
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""

    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


def create_pagination_response(
    items: List[T],
    total: int,
    page: int,
    page_size: int,
) -> PaginatedResponse[T]:
    """Create a paginated response."""
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


# Invoice Schemas
class InvoiceLineBase(BaseModel):
    """Base schema for invoice line items."""

    line_number: int
    description: str
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    unit_of_measure: str = "EA"
    quantity: Decimal
    quantity_received: Decimal = Decimal("0")
    unit_price: Decimal
    line_total: Decimal
    tax_rate: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    po_line_ref: Optional[str] = None
    dn_line_ref: Optional[str] = None


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating an invoice line."""

    pass


class InvoiceLineResponse(InvoiceLineBase):
    """Schema for invoice line response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    invoice_id: uuid.UUID
    matched_po_line_id: Optional[uuid.UUID] = None
    matched_dn_line_id: Optional[uuid.UUID] = None
    match_score: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime


class InvoiceBase(BaseModel):
    """Base schema for invoices."""

    vendor_id: str
    vendor_name: str
    vendor_tax_id: Optional[str] = None
    invoice_number: str
    invoice_date: date
    due_date: Optional[date] = None
    receipt_date: Optional[date] = None
    subtotal: Decimal
    tax_amount: Decimal = Decimal("0")
    total_amount: Decimal
    currency_code: str = "USD"
    purchase_order_ref: Optional[str] = None
    delivery_note_ref: Optional[str] = None
    payment_terms: Optional[str] = None
    notes: Optional[str] = None
    source_system: str = "manual"


class InvoiceCreate(InvoiceBase):
    """Schema for creating an invoice."""

    lines: List[InvoiceLineCreate] = Field(default_factory=list)


class InvoiceUpdate(BaseModel):
    """Schema for updating an invoice."""

    status: Optional[str] = None
    notes: Optional[str] = None
    due_date: Optional[date] = None


class InvoiceResponse(InvoiceBase):
    """Schema for invoice response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    match_score: Optional[Decimal] = None
    match_decision: Optional[str] = None
    matched_po_id: Optional[uuid.UUID] = None
    matched_dn_id: Optional[uuid.UUID] = None
    has_exception: bool
    exception_id: Optional[uuid.UUID] = None
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    lines: List[InvoiceLineResponse] = Field(default_factory=list)


# Purchase Order Schemas
class POLineBase(BaseModel):
    """Base schema for PO line items."""

    line_number: int
    description: str
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    unit_of_measure: str = "EA"
    quantity_ordered: Decimal
    quantity_delivered: Decimal = Decimal("0")
    quantity_invoiced: Decimal = Decimal("0")
    unit_price: Decimal
    line_total: Decimal
    tax_rate: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    delivery_date: Optional[date] = None


class POLineCreate(POLineBase):
    """Schema for creating a PO line."""

    pass


class POLineResponse(POLineBase):
    """Schema for PO line response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    po_id: uuid.UUID
    is_fully_delivered: bool
    is_fully_invoiced: bool
    created_at: datetime
    updated_at: datetime


class PurchaseOrderBase(BaseModel):
    """Base schema for purchase orders."""

    vendor_id: str
    vendor_name: str
    vendor_tax_id: Optional[str] = None
    po_number: str
    po_date: date
    delivery_date: Optional[date] = None
    subtotal: Decimal
    tax_amount: Decimal = Decimal("0")
    total_amount: Decimal
    currency_code: str = "USD"
    requisition_id: Optional[str] = None
    project_code: Optional[str] = None
    cost_center: Optional[str] = None
    payment_terms: Optional[str] = None
    notes: Optional[str] = None
    source_system: str = "erp"


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a purchase order."""

    lines: List[POLineCreate] = Field(default_factory=list)


class PurchaseOrderResponse(PurchaseOrderBase):
    """Schema for purchase order response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    is_fully_delivered: bool
    is_fully_invoiced: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    lines: List[POLineResponse] = Field(default_factory=list)


# Delivery Note Schemas
class DNLineBase(BaseModel):
    """Base schema for delivery note line items."""

    line_number: int
    description: str
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    unit_of_measure: str = "EA"
    quantity_delivered: Decimal
    quantity_received: Decimal = Decimal("0")
    unit_price: Optional[Decimal] = None
    line_total: Decimal
    po_line_ref: Optional[str] = None
    delivery_date: Optional[date] = None
    is_accepted: bool = True


class DNLineCreate(DNLineBase):
    """Schema for creating a DN line."""

    pass


class DNLineResponse(DNLineBase):
    """Schema for DN line response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    dn_id: uuid.UUID
    matched_po_line_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime


class DeliveryNoteBase(BaseModel):
    """Base schema for delivery notes."""

    vendor_id: str
    vendor_name: str
    vendor_tax_id: Optional[str] = None
    dn_number: str
    dn_date: date
    receipt_date: Optional[date] = None
    po_ref: Optional[str] = None
    subtotal: Decimal
    total_amount: Decimal
    currency_code: str = "USD"
    notes: Optional[str] = None
    source_system: str = "erp"


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating a delivery note."""

    lines: List[DNLineCreate] = Field(default_factory=list)


class DeliveryNoteResponse(DeliveryNoteBase):
    """Schema for delivery note response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    matched_po_id: Optional[uuid.UUID] = None
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    lines: List[DNLineResponse] = Field(default_factory=list)


# Matching Schemas
class MatchResultLine(BaseModel):
    """Result for a single line match."""

    invoice_line_id: uuid.UUID
    po_line_id: Optional[uuid.UUID] = None
    dn_line_id: Optional[uuid.UUID] = None
    match_score: Decimal
    price_match: bool
    quantity_match: bool
    status: str


class MatchResult(BaseModel):
    """Result of matching operation."""

    invoice_id: uuid.UUID
    overall_score: Decimal
    decision: str
    confidence: str
    lines: List[MatchResultLine]
    has_exception: bool
    exception_type: Optional[str] = None
    exception_message: Optional[str] = None


class MatchTriggerRequest(BaseModel):
    """Request to trigger matching for an invoice."""

    invoice_id: uuid.UUID
    force_rematch: bool = False


class MatchDecisionRequest(BaseModel):
    """Request to record a match decision."""

    invoice_id: uuid.UUID
    decision: str
    po_id: Optional[uuid.UUID] = None
    dn_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None


# Balance Ledger Schemas
class BalanceLedgerResponse(BaseModel):
    """Schema for balance ledger response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    po_line_id: uuid.UUID
    po_id: uuid.UUID
    product_code: Optional[str] = None
    vendor_id: str
    original_ordered_qty: Decimal
    delivered_qty: Decimal
    invoiced_qty: Decimal
    paid_qty: Decimal
    original_amount: Decimal
    delivered_amount: Decimal
    invoiced_amount: Decimal
    paid_amount: Decimal
    balance_qty: Decimal
    balance_amount: Decimal
    delivery_balance_qty: Decimal
    delivery_balance_amount: Decimal
    invoice_balance_qty: Decimal
    invoice_balance_amount: Decimal
    is_fully_delivered: bool
    is_fully_invoiced: bool
    is_fully_paid: bool
    po_date: date
    po_delivery_date: Optional[date] = None
    last_invoice_id: Optional[uuid.UUID] = None
    last_invoice_date: Optional[date] = None
    last_delivery_id: Optional[uuid.UUID] = None
    last_delivery_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime


# Exception Schemas
class ExceptionBase(BaseModel):
    """Base schema for exceptions."""

    invoice_id: uuid.UUID
    exception_type: str
    message: str
    po_id: Optional[uuid.UUID] = None
    dn_id: Optional[uuid.UUID] = None


class ExceptionCreate(ExceptionBase):
    """Schema for creating an exception."""

    pass


class ExceptionResponse(ExceptionBase):
    """Schema for exception response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ExceptionResolveRequest(BaseModel):
    """Request to resolve an exception."""

    resolution_notes: str


class ExceptionDismissRequest(BaseModel):
    """Request to dismiss an exception."""

    reason: str


# Cross Reference Schemas
class CrossRefResponse(BaseModel):
    """Schema for cross reference response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_code: Optional[str] = None
    vendor_id: str
    po_product_code: Optional[str] = None
    invoice_product_code: Optional[str] = None
    unit_price_po: Optional[Decimal] = None
    unit_price_invoice: Optional[Decimal] = None
    quantity_ratio: Optional[Decimal] = None
    match_score: Decimal
    match_decision: str
    confirmation_count: int
    rejection_count: int
    status: str
    confidence_score: Decimal
    is_promoted: bool
    promoted_at: Optional[datetime] = None
    first_match_date: date
    last_match_date: date
    is_active: bool
    created_at: datetime
    updated_at: datetime


# Common Schemas
class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    database: str


class ErrorResponse(BaseModel):
    """Error response schema."""

    detail: str
    code: Optional[str] = None
    field: Optional[str] = None


class SuccessResponse(BaseModel):
    """Generic success response."""

    success: bool = True
    message: str
    data: Optional[dict] = None

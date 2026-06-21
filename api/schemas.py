// api/schemas.py
"""Shared Pydantic schemas for API request/response models."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# Generic type for paginated responses
T = TypeVar("T")


# ============== Common Schemas ==============

class ErrorResponse(BaseModel):
    """Standard error response schema."""
    
    error: str
    detail: str | None = None
    code: str | None = None


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""
    
    data: list[T]
    meta: PaginationMeta


# ============== Invoice Schemas ==============

class InvoiceLineItemBase(BaseModel):
    """Base schema for invoice line items."""
    
    line_number: int
    description: str = Field(max_length=500)
    quantity: Decimal = Field(ge=0, decimal_places=4)
    unit_price: Decimal = Field(ge=0, decimal_places=4)
    amount: Decimal = Field(ge=0, decimal_places=2)
    uom: str | None = Field(default=None, max_length=20)
    tax_code: str | None = Field(default=None, max_length=50)


class InvoiceLineItemCreate(InvoiceLineItemBase):
    """Schema for creating invoice line items."""
    pass


class InvoiceLineItemResponse(InvoiceLineItemBase):
    """Schema for invoice line item responses."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID


class InvoiceBase(BaseModel):
    """Base schema for invoices."""
    
    invoice_number: str = Field(max_length=100)
    supplier_id: str = Field(max_length=100)
    supplier_name: str = Field(max_length=255)
    invoice_date: date
    due_date: date | None = None
    total_amount: Decimal = Field(ge=0, decimal_places=2)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)
    currency: str = Field(default="USD", max_length=3)
    notes: str | None = None
    erp_reference: str | None = Field(default=None, max_length=255)


class InvoiceCreate(InvoiceBase):
    """Schema for creating invoices."""
    
    line_items: list[InvoiceLineItemCreate] = []


class InvoiceUpdate(BaseModel):
    """Schema for updating invoices."""
    
    status: str | None = None
    notes: str | None = None
    match_decision: str | None = None


class InvoiceResponse(InvoiceBase):
    """Schema for invoice responses."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    status: str
    matched_po_id: UUID | None = None
    match_score: float | None = None
    match_decision: str | None = None
    received_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class InvoiceDetailResponse(InvoiceResponse):
    """Detailed invoice response with line items."""
    
    model_config = ConfigDict(from_attributes=True)
    
    line_items: list[InvoiceLineItemResponse] = []


# ============== Purchase Order Schemas ==============

class POLineItemBase(BaseModel):
    """Base schema for PO line items."""
    
    line_number: int
    description: str = Field(max_length=500)
    quantity: Decimal = Field(ge=0, decimal_places=4)
    unit_price: Decimal = Field(ge=0, decimal_places=4)
    amount: Decimal = Field(ge=0, decimal_places=2)
    uom: str | None = Field(default=None, max_length=20)
    tax_code: str | None = Field(default=None, max_length=50)
    delivery_date: date | None = None


class POLineItemCreate(POLineItemBase):
    """Schema for creating PO line items."""
    pass


class POLineItemResponse(POLineItemBase):
    """Schema for PO line item responses."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID


class PurchaseOrderBase(BaseModel):
    """Base schema for purchase orders."""
    
    po_number: str = Field(max_length=100)
    supplier_id: str = Field(max_length=100)
    supplier_name: str = Field(max_length=255)
    order_date: date
    delivery_date: date | None = None
    total_amount: Decimal = Field(ge=0, decimal_places=2)
    currency: str = Field(default="USD", max_length=3)
    notes: str | None = None
    erp_reference: str | None = Field(default=None, max_length=255)


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating purchase orders."""
    
    line_items: list[POLineItemCreate] = []


class PurchaseOrderResponse(PurchaseOrderBase):
    """Schema for purchase order responses."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    status: str
    is_anchored: bool
    created_at: datetime
    updated_at: datetime


class PurchaseOrderDetailResponse(PurchaseOrderResponse):
    """Detailed PO response with line items."""
    
    model_config = ConfigDict(from_attributes=True)
    
    line_items: list[POLineItemResponse] = []


# ============== Delivery Note Schemas ==============

class DNLineItemBase(BaseModel):
    """Base schema for delivery note line items."""
    
    line_number: int
    description: str = Field(max_length=500)
    quantity: Decimal = Field(ge=0, decimal_places=4)
    uom: str | None = Field(default=None, max_length=20)
    notes: str | None = None
    po_line_id: UUID | None = None


class DNLineItemCreate(DNLineItemBase):
    """Schema for creating delivery note line items."""
    pass


class DNLineItemResponse(DNLineItemBase):
    """Schema for delivery note line item responses."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID


class DeliveryNoteBase(BaseModel):
    """Base schema for delivery notes."""
    
    dn_number: str = Field(max_length=100)
    supplier_id: str = Field(max_length=100)
    supplier_name: str = Field(max_length=255)
    delivery_date: date
    received_date: date | None = None
    total_amount: Decimal = Field(ge=0, decimal_places=2)
    currency: str = Field(default="USD", max_length=3)
    notes: str | None = None
    erp_reference: str | None = Field(default=None, max_length=255)


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating delivery notes."""
    
    po_id: UUID | None = None
    line_items: list[DNLineItemCreate] = []


class DeliveryNoteResponse(DeliveryNoteBase):
    """Schema for delivery note responses."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    po_id: UUID | None = None
    status: str
    created_at: datetime
    updated_at: datetime


class DeliveryNoteDetailResponse(DeliveryNoteResponse):
    """Detailed delivery note response with line items."""
    
    model_config = ConfigDict(from_attributes=True)
    
    line_items: list[DNLineItemResponse] = []


# ============== Matching Schemas ==============

class MatchingRequest(BaseModel):
    """Schema for triggering invoice matching."""
    
    invoice_id: UUID


class LineMatchDetail(BaseModel):
    """Detail of a line-level match."""
    
    invoice_line_number: int
    po_line_id: UUID
    quantity_matched: Decimal
    match_score: float


class MatchingResponse(BaseModel):
    """Schema for matching response."""
    
    invoice_id: UUID
    po_id: UUID | None
    match_score: float
    decision: str
    line_matches: list[LineMatchDetail]
    total_amount: Decimal
    matched_amount: Decimal
    variance_amount: Decimal
    variance_percentage: float
    requires_review: bool


# ============== Exception Schemas ==============

class ExceptionBase(BaseModel):
    """Base schema for exceptions."""
    
    exception_type: str
    invoice_id: UUID
    po_id: UUID | None = None
    po_line_id: UUID | None = None
    message: str
    field_name: str | None = None
    expected_value: Any | None = None
    actual_value: Any | None = None


class ExceptionResponse(ExceptionBase):
    """Schema for exception responses."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    status: str
    resolved_by: str | None = None
    resolved_at: datetime | None = None
    resolution_notes: str | None = None
    created_at: datetime
    updated_at: datetime


class ExceptionResolveRequest(BaseModel):
    """Schema for resolving an exception."""
    
    resolution_notes: str | None = Field(default=None, max_length=500)
    resolved_by: str | None = Field(default=None, max_length=100)


# ============== Balance Schemas ==============

class BalanceEntryResponse(BaseModel):
    """Schema for balance ledger entry response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    po_id: UUID
    po_line_id: UUID | None
    invoice_id: UUID | None
    transaction_type: str
    amount: Decimal
    running_balance: Decimal
    transaction_date: date
    notes: str | None
    created_at: datetime


class BalanceResponse(BaseModel):
    """Schema for balance response."""
    
    po_id: UUID
    po_number: str
    po_total_amount: Decimal
    total_invoiced: Decimal
    remaining_balance: Decimal
    balance_percentage: float
    line_balances: list[dict[str, Any]]


# ============== Cross-Reference Schemas ==============

class CrossRefResponse(BaseModel):
    """Schema for cross-reference response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    po_id: UUID
    po_line_id: UUID
    supplier_id: str
    supplier_part_number: str | None
    po_part_description: str
    match_count: int
    total_quantity: Decimal
    average_price: Decimal | None
    last_matched_at: datetime
    is_promoted: bool
    confidence_score: float
    is_active: bool

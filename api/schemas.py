# api/schemas.py
"""Shared Pydantic schemas for request/response models."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""
    
    model_config = ConfigDict(from_attributes=True)
    
    success: bool = True
    message: str | None = None
    data: T | None = None
    error: str | None = None


class ErrorResponse(BaseModel):
    """Error response schema."""
    
    success: bool = False
    error: str
    detail: str | None = None
    code: str | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int


class PaginationParams(BaseModel):
    """Pagination parameters."""
    
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    
    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.page_size


# Invoice Schemas

class InvoiceLineBase(BaseModel):
    """Base schema for invoice line items."""
    
    line_number: int
    description: str
    quantity: Decimal = Field(ge=0)
    unit_of_measure: str | None = "EA"
    unit_price: Decimal = Field(ge=0)
    line_amount: Decimal = Field(ge=0)
    tax_rate: Decimal = Field(default=Decimal("0.0000"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    sku: str | None = None
    po_line_id: UUID | None = None
    dn_line_id: UUID | None = None


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating invoice line items."""
    pass


class InvoiceLineResponse(InvoiceLineBase):
    """Schema for invoice line item responses."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    invoice_id: UUID
    matched_quantity: Decimal | None = None
    matched_amount: Decimal | None = None
    price_variance: Decimal | None = None
    quantity_variance: Decimal | None = None
    match_score: float | None = None
    created_at: datetime
    updated_at: datetime


class InvoiceBase(BaseModel):
    """Base schema for invoices."""
    
    vendor_id: str
    vendor_name: str | None = None
    invoice_number: str
    invoice_date: date
    due_date: date | None = None
    subtotal: Decimal = Field(ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    total_amount: Decimal = Field(ge=0)
    currency: str = "USD"
    source: str = "manual"
    source_reference: str | None = None
    notes: str | None = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating invoices."""
    
    lines: list[InvoiceLineCreate] = Field(min_length=1)
    
    @field_validator("lines")
    @classmethod
    def validate_lines(cls, v: list[InvoiceLineCreate]) -> list[InvoiceLineCreate]:
        """Ensure line numbers are unique and sequential."""
        line_numbers = [line.line_number for line in v]
        if len(line_numbers) != len(set(line_numbers)):
            raise ValueError("Line numbers must be unique")
        return sorted(v, key=lambda x: x.line_number)


class InvoiceUpdate(BaseModel):
    """Schema for updating invoices."""
    
    vendor_id: str | None = None
    vendor_name: str | None = None
    due_date: date | None = None
    status: str | None = None
    notes: str | None = None


class InvoiceResponse(InvoiceBase):
    """Schema for invoice responses."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    status: str
    matched_amount: Decimal | None = None
    match_score: float | None = None
    match_decision: str | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    paid_at: datetime | None = None
    payment_reference: str | None = None
    created_at: datetime
    updated_at: datetime
    lines: list[InvoiceLineResponse] = []


# Purchase Order Schemas

class PurchaseOrderLineBase(BaseModel):
    """Base schema for PO line items."""
    
    line_number: int
    description: str
    sku: str | None = None
    vendor_sku: str | None = None
    category: str | None = None
    quantity_ordered: Decimal = Field(gt=0)
    unit_of_measure: str = "EA"
    unit_price: Decimal = Field(ge=0)
    line_amount: Decimal = Field(ge=0)
    tax_rate: Decimal = Field(default=Decimal("0.0000"), ge=0)


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Schema for creating PO line items."""
    pass


class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    """Schema for PO line item responses."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    po_id: UUID
    quantity_received: Decimal | None = None
    quantity_invoiced: Decimal | None = None
    remaining_quantity: Decimal | None = None
    remaining_amount: Decimal | None = None
    created_at: datetime
    updated_at: datetime


class PurchaseOrderBase(BaseModel):
    """Base schema for purchase orders."""
    
    vendor_id: str
    vendor_name: str | None = None
    vendor_tax_id: str | None = None
    po_number: str
    po_date: date
    delivery_date: date | None = None
    subtotal: Decimal = Field(ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    total_amount: Decimal = Field(ge=0)
    currency: str = "USD"
    source: str = "erp"
    source_reference: str | None = None
    payment_terms: str | None = None
    delivery_terms: str | None = None
    notes: str | None = None
    ship_to: str | None = None
    bill_to: str | None = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating purchase orders."""
    
    lines: list[PurchaseOrderLineCreate] = Field(min_length=1)


class PurchaseOrderResponse(PurchaseOrderBase):
    """Schema for PO responses."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    lines: list[PurchaseOrderLineResponse] = []


# Delivery Note Schemas

class DeliveryNoteLineBase(BaseModel):
    """Base schema for delivery note line items."""
    
    line_number: int
    description: str
    sku: str | None = None
    vendor_sku: str | None = None
    quantity_delivered: Decimal = Field(gt=0)
    unit_of_measure: str = "EA"
    unit_price: Decimal | None = None
    line_amount: Decimal | None = None
    po_line_id: UUID | None = None


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating delivery note line items."""
    pass


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """Schema for delivery note line item responses."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    dn_id: UUID
    quantity_invoiced: Decimal | None = None
    created_at: datetime
    updated_at: datetime


class DeliveryNoteBase(BaseModel):
    """Base schema for delivery notes."""
    
    vendor_id: str
    vendor_name: str | None = None
    po_id: UUID | None = None
    dn_number: str
    dn_date: date
    received_date: date | None = None
    total_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    currency: str = "USD"
    source: str = "erp"
    source_reference: str | None = None
    carrier: str | None = None
    tracking_number: str | None = None
    number_of_packages: int | None = None
    notes: str | None = None
    received_by: str | None = None
    condition: str | None = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating delivery notes."""
    
    lines: list[DeliveryNoteLineCreate] = Field(min_length=1)


class DeliveryNoteResponse(DeliveryNoteBase):
    """Schema for delivery note responses."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    lines: list[DeliveryNoteLineResponse] = []


# Matching Schemas

class MatchingRequest(BaseModel):
    """Schema for triggering matching."""
    
    invoice_id: UUID
    auto_approve_threshold: float | None = None
    force_rematch: bool = False


class MatchingResult(BaseModel):
    """Schema for matching result per line."""
    
    invoice_line_id: UUID
    po_line_id: UUID | None
    dn_line_id: UUID | None = None
    match_score: float
    price_match: bool
    quantity_match: bool
    price_variance_pct: float | None = None
    quantity_variance_pct: float | None = None
    decision: str
    confidence: str


class MatchingResponse(BaseModel):
    """Schema for matching response."""
    
    invoice_id: UUID
    decision: str
    overall_score: float
    total_matched_amount: Decimal
    total_invoice_amount: Decimal
    match_percentage: float
    line_results: list[MatchingResult]
    exception_ids: list[UUID] = []


# Exception Schemas

class ExceptionBase(BaseModel):
    """Base schema for exceptions."""
    
    exception_type: str
    description: str
    invoice_id: UUID
    po_id: UUID | None = None
    po_line_id: UUID | None = None
    invoice_line_id: UUID | None = None
    expected_value: Decimal | None = None
    actual_value: Decimal | None = None
    variance: Decimal | None = None
    variance_percentage: float | None = None
    notes: str | None = None


class ExceptionCreate(ExceptionBase):
    """Schema for creating exceptions."""
    pass


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


class ExceptionResolve(BaseModel):
    """Schema for resolving exceptions."""
    
    resolution_notes: str | None = None
    resolution_action: str | None = None


# Balance Ledger Schemas

class BalanceLedgerResponse(BaseModel):
    """Schema for balance ledger responses."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    po_line_id: UUID
    invoice_line_id: UUID | None
    transaction_type: str
    transaction_reference: str
    quantity_before: Decimal
    quantity_change: Decimal
    quantity_after: Decimal
    amount_before: Decimal
    amount_change: Decimal
    amount_after: Decimal
    currency: str
    notes: str | None = None
    processed_by: str | None = None
    created_at: datetime


# Health Check Schema

class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str
    version: str
    database: str
    timestamp: datetime

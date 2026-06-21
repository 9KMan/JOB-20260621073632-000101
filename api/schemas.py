# api/schemas.py
"""Shared Pydantic request/response models for the API."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    """Base response wrapper for all API responses."""
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "success": True,
                "data": {},
                "message": "Operation completed successfully",
            }
        },
    )
    
    success: bool = Field(default=True, description="Whether the operation succeeded")
    data: T | None = Field(default=None, description="Response payload")
    message: str | None = Field(default=None, description="Human-readable message")
    error: str | None = Field(default=None, description="Error message if failed")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    
    model_config = ConfigDict(from_attributes=True)
    
    success: bool = True
    data: list[T]
    total: int = Field(description="Total number of records")
    page: int = Field(description="Current page number")
    per_page: int = Field(description="Items per page")
    pages: int = Field(description="Total number of pages")


class ErrorResponse(BaseModel):
    """Standard error response."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error": "Invoice not found",
                "detail": "No invoice with ID 123e4567-e89b-12d3-a456-426614174000",
            }
        },
    )
    
    success: bool = False
    error: str = Field(description="Error type")
    detail: str | None = Field(default=None, description="Detailed error message")


class HealthCheckResponse(BaseModel):
    """Health check response."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "database": "connected",
                "version": "1.0.0",
            }
        },
    )
    
    status: str = Field(description="Overall health status")
    database: str = Field(description="Database connection status")
    version: str = Field(description="Application version")


# ============ Invoice Schemas ============

class InvoiceLineBase(BaseModel):
    """Base schema for invoice line items."""
    
    line_number: int = Field(..., ge=1, description="Line item number")
    description: str = Field(..., max_length=500, description="Line description")
    quantity: Decimal = Field(..., ge=0, description="Quantity invoiced")
    unit_of_measure: str | None = Field(default=None, max_length=20)
    unit_price: Decimal = Field(..., ge=0, description="Unit price")
    net_amount: Decimal = Field(..., ge=0, description="Net line amount")
    tax_amount: Decimal = Field(default=Decimal("0"), ge=0)
    tax_rate: Decimal = Field(default=Decimal("0"), ge=0)


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating invoice line items."""
    pass


class InvoiceLineResponse(InvoiceLineBase):
    """Schema for invoice line response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    po_line_id: UUID | None = None
    delivery_note_line_id: UUID | None = None
    matched_quantity: Decimal
    match_score: int | None = None


class InvoiceBase(BaseModel):
    """Base schema for invoices."""
    
    invoice_number: str = Field(..., max_length=50, description="Unique invoice number")
    vendor_id: str = Field(..., max_length=50, description="Vendor identifier")
    vendor_name: str = Field(..., max_length=200)
    invoice_date: date = Field(..., description="Invoice date")
    due_date: date | None = Field(default=None)
    currency: str = Field(default="USD", max_length=3)
    total_amount: Decimal = Field(..., ge=0)
    subtotal: Decimal = Field(default=Decimal("0"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0"), ge=0)
    tax_exclusive: bool = Field(default=True)
    payment_terms: str | None = Field(default=None, max_length=100)
    notes: str | None = None
    purchase_order_id: UUID | None = None
    source_system: str = Field(default="manual", max_length=50)
    metadata: dict[str, Any] | None = Field(default=None)
    lines: list[InvoiceLineCreate] = Field(..., min_length=1)


class InvoiceCreate(InvoiceBase):
    """Schema for creating invoices."""
    
    @field_validator("invoice_number")
    @classmethod
    def invoice_number_upper(cls, v: str) -> str:
        return v.upper().strip()


class InvoiceUpdate(BaseModel):
    """Schema for updating invoices."""
    
    status: str | None = None
    match_decision: str | None = None
    exception_reason: str | None = None
    approved_by: UUID | None = None
    notes: str | None = None


class InvoiceResponse(BaseModel):
    """Schema for invoice response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    invoice_number: str
    vendor_id: str
    vendor_name: str
    invoice_date: date
    due_date: date | None
    status: str
    currency: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    purchase_order_id: UUID | None
    match_decision: str | None
    match_score: int | None
    exception_reason: str | None
    approved_by: UUID | None
    approved_at: datetime | None
    source_system: str
    created_at: datetime
    lines: list[InvoiceLineResponse]


# ============ Purchase Order Schemas ============

class POLineBase(BaseModel):
    """Base schema for PO line items."""
    
    line_number: int = Field(..., ge=1)
    description: str = Field(..., max_length=500)
    quantity: Decimal = Field(..., ge=0)
    unit_of_measure: str | None = Field(default=None, max_length=20)
    unit_price: Decimal = Field(..., ge=0)
    net_amount: Decimal = Field(..., ge=0)
    tax_amount: Decimal = Field(default=Decimal("0"), ge=0)
    tax_rate: Decimal = Field(default=Decimal("0"), ge=0)
    promised_date: date | None = None


class POLineCreate(POLineBase):
    """Schema for creating PO line items."""
    pass


class POLineResponse(POLineBase):
    """Schema for PO line response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    received_quantity: Decimal
    invoiced_quantity: Decimal
    line_status: str


class PurchaseOrderBase(BaseModel):
    """Base schema for purchase orders."""
    
    po_number: str = Field(..., max_length=50)
    vendor_id: str = Field(..., max_length=50)
    vendor_name: str = Field(..., max_length=200)
    order_date: date
    expected_delivery_date: date | None = None
    currency: str = Field(default="USD", max_length=3)
    total_amount: Decimal = Field(..., ge=0)
    subtotal: Decimal = Field(default=Decimal("0"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0"), ge=0)
    payment_terms: str | None = Field(default=None, max_length=100)
    shipping_address: str | None = None
    notes: str | None = None
    source_system: str = Field(default="erp", max_length=50)
    metadata: dict[str, Any] | None = None
    lines: list[POLineCreate] = Field(..., min_length=1)


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating purchase orders."""
    
    @field_validator("po_number")
    @classmethod
    def po_number_upper(cls, v: str) -> str:
        return v.upper().strip()


class PurchaseOrderResponse(PurchaseOrderBase):
    """Schema for purchase order response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    status: str
    created_at: datetime
    lines: list[POLineResponse]


# ============ Delivery Note Schemas ============

class DeliveryNoteLineBase(BaseModel):
    """Base schema for delivery note line items."""
    
    line_number: int = Field(..., ge=1)
    description: str = Field(..., max_length=500)
    quantity: Decimal = Field(..., ge=0)
    unit_of_measure: str | None = Field(default=None, max_length=20)
    po_line_id: UUID | None = None


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating delivery note line items."""
    pass


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """Schema for delivery note line response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    invoiced_quantity: Decimal
    line_status: str


class DeliveryNoteBase(BaseModel):
    """Base schema for delivery notes."""
    
    dn_number: str = Field(..., max_length=50)
    vendor_id: str = Field(..., max_length=50)
    vendor_name: str = Field(..., max_length=200)
    po_number: str | None = Field(default=None, max_length=50)
    delivery_date: date
    currency: str = Field(default="USD", max_length=3)
    total_amount: Decimal = Field(default=Decimal("0"), ge=0)
    notes: str | None = None
    source_system: str = Field(default="erp", max_length=50)
    metadata: dict[str, Any] | None = None
    lines: list[DeliveryNoteLineCreate] = Field(..., min_length=1)


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating delivery notes."""
    
    @field_validator("dn_number")
    @classmethod
    def dn_number_upper(cls, v: str) -> str:
        return v.upper().strip()


class DeliveryNoteResponse(DeliveryNoteBase):
    """Schema for delivery note response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    status: str
    created_at: datetime
    lines: list[DeliveryNoteLineResponse]


# ============ Matching Schemas ============

class MatchTriggerRequest(BaseModel):
    """Request to trigger matching for an invoice."""
    
    invoice_id: UUID = Field(..., description="Invoice ID to match")
    match_all_lines: bool = Field(
        default=True,
        description="Whether to attempt matching all lines",
    )


class MatchResultLine(BaseModel):
    """Match result for a single invoice line."""
    
    invoice_line_id: UUID
    line_number: int
    match_status: str
    po_line_id: UUID | None = None
    po_line_number: int | None = None
    delivery_note_line_id: UUID | None = None
    match_score: int
    price_variance_pct: Decimal
    quantity_variance_pct: Decimal
    description_match: str


class MatchResult(BaseModel):
    """Result of matching operation."""
    
    invoice_id: UUID
    invoice_number: str
    match_status: str
    decision: str
    overall_score: int
    lines: list[MatchResultLine]
    exception_reason: str | None = None


class MatchDecisionRequest(BaseModel):
    """Request to make a match decision."""
    
    invoice_id: UUID = Field(..., description="Invoice ID")
    decision: str = Field(
        ...,
        description="Decision: approve, reject, exception",
    )
    reason: str | None = Field(default=None, description="Reason for decision")
    override_threshold: bool = Field(
        default=False,
        description="Whether to override scoring threshold",
    )


# ============ Exception Schemas ============

class ExceptionItem(BaseModel):
    """Exception item in the exceptions list."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    invoice_id: UUID
    invoice_number: str
    vendor_id: str
    vendor_name: str
    exception_type: str
    exception_reason: str
    match_score: int | None
    created_at: datetime
    resolved: bool
    resolved_by: UUID | None
    resolved_at: datetime | None
    resolution_notes: str | None


class ExceptionResolveRequest(BaseModel):
    """Request to resolve an exception."""
    
    invoice_id: UUID = Field(..., description="Invoice ID")
    resolution_type: str = Field(
        ...,
        description="Resolution type: approve, reject, adjust",
    )
    notes: str | None = Field(default=None, description="Resolution notes")
    adjusted_amount: Decimal | None = Field(default=None, description="Adjusted amount if applicable")


class ExceptionDismissRequest(BaseModel):
    """Request to dismiss an exception."""
    
    invoice_id: UUID = Field(..., description="Invoice ID")
    reason: str = Field(..., description="Reason for dismissal")
    dismiss_as_approved: bool = Field(
        default=False,
        description="Dismiss as approved or rejected",
    )


# ============ Balance Ledger Schemas ============

class BalanceLedgerEntry(BaseModel):
    """Balance ledger entry response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    invoice_id: UUID
    invoice_number: str
    po_line_id: UUID
    po_number: str
    po_line_number: int
    po_quantity: Decimal
    delivered_quantity: Decimal
    invoiced_quantity: Decimal
    previous_invoiced: Decimal
    po_amount: Decimal
    invoiced_amount: Decimal
    quantity_balance: Decimal
    amount_balance: Decimal
    balance_status: str


class BalanceSummary(BaseModel):
    """Balance summary for a PO line."""
    
    po_line_id: UUID
    po_number: str
    line_number: int
    po_quantity: Decimal
    total_delivered: Decimal
    total_invoiced: Decimal
    remaining_quantity: Decimal
    balance_status: str

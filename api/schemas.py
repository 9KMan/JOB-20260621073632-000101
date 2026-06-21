# api/schemas.py
"""Shared Pydantic request/response schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    """Base response wrapper for all API responses."""
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )
    
    success: bool = Field(default=True, description="Whether the request succeeded")
    data: T | None = Field(default=None, description="Response data")
    message: str | None = Field(default=None, description="Optional message")
    error: ErrorResponse | None = Field(default=None, description="Error details if failed")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    
    model_config = ConfigDict(from_attributes=True)
    
    success: bool = Field(default=True)
    data: list[T] = Field(default_factory=list)
    total: int = Field(default=0, description="Total number of items")
    page: int = Field(default=1, ge=1, description="Current page")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    pages: int = Field(default=0, description="Total number of pages")
    has_next: bool = Field(default=False, description="Whether there are more pages")
    has_prev: bool = Field(default=False, description="Whether there are previous pages")


class ErrorResponse(BaseModel):
    """Error response schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    code: str = Field(description="Error code")
    message: str = Field(description="Human-readable error message")
    details: dict[str, Any] | None = Field(default=None, description="Additional details")
    field: str | None = Field(default=None, description="Field that caused the error")


class HealthResponse(BaseModel):
    """Health check response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    status: str = Field(description="Service status")
    version: str = Field(description="Application version")
    timestamp: datetime = Field(description="Current server time")
    database: str = Field(description="Database connection status")
    checks: dict[str, bool] = Field(default_factory=dict, description="Individual health checks")


# Invoice Schemas
class InvoiceLineBase(BaseModel):
    """Base invoice line schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    line_number: str
    sku: str | None = None
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal
    tax_rate: Decimal = Decimal("0.0000")
    tax_amount: Decimal = Decimal("0.00")


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating invoice line."""
    
    pass


class InvoiceLineResponse(InvoiceLineBase):
    """Schema for invoice line response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    invoice_id: UUID
    matched_po_line_id: UUID | None = None
    matched_dn_line_id: UUID | None = None
    match_type: str | None = None
    match_score: int | None = None
    status: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class InvoiceBase(BaseModel):
    """Base invoice schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    invoice_number: str
    vendor_id: str
    vendor_name: str
    invoice_date: date
    due_date: date | None = None
    received_date: date | None = None
    subtotal: Decimal = Decimal("0.00")
    tax_amount: Decimal = Decimal("0.00")
    total_amount: Decimal
    currency: str = "USD"
    exchange_rate: Decimal = Decimal("1.000000")
    notes: str | None = None
    erp_invoice_id: str | None = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating invoice."""
    
    model_config = ConfigDict(from_attributes=True)
    
    lines: list[InvoiceLineCreate] = Field(default_factory=list)


class InvoiceUpdate(BaseModel):
    """Schema for updating invoice."""
    
    model_config = ConfigDict(from_attributes=True)
    
    status: str | None = None
    notes: str | None = None
    approved_by: str | None = None


class InvoiceResponse(InvoiceBase):
    """Schema for invoice response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    status: str
    matched_po_id: UUID | None = None
    matched_dn_id: UUID | None = None
    match_decision: str | None = None
    match_score: int | None = None
    matched_at: datetime | None = None
    exception_count: int = 0
    approved_by: str | None = None
    approved_at: datetime | None = None
    rejection_reason: str | None = None
    lines: list[InvoiceLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class InvoiceListResponse(BaseModel):
    """Schema for invoice list item (without lines)."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    invoice_number: str
    vendor_id: str
    vendor_name: str
    invoice_date: date
    total_amount: Decimal
    currency: str
    status: str
    match_decision: str | None = None
    match_score: int | None = None
    exception_count: int = 0
    created_at: datetime


# Purchase Order Schemas
class POLineBase(BaseModel):
    """Base PO line schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    line_number: str
    sku: str | None = None
    description: str
    category: str | None = None
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal
    tax_rate: Decimal = Decimal("0.0000")


class POLineCreate(POLineBase):
    """Schema for creating PO line."""
    
    pass


class POLineResponse(POLineBase):
    """Schema for PO line response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    purchase_order_id: UUID
    received_quantity: Decimal
    invoiced_quantity: Decimal
    status: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class PurchaseOrderBase(BaseModel):
    """Base purchase order schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    po_number: str
    vendor_id: str
    vendor_name: str
    po_date: date
    delivery_date: date | None = None
    expiry_date: date | None = None
    subtotal: Decimal = Decimal("0.00")
    tax_amount: Decimal = Decimal("0.00")
    total_amount: Decimal
    currency: str = "USD"
    notes: str | None = None
    erp_po_id: str | None = None
    department_code: str | None = None
    cost_center: str | None = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating purchase order."""
    
    model_config = ConfigDict(from_attributes=True)
    
    lines: list[POLineCreate] = Field(default_factory=list)


class PurchaseOrderResponse(PurchaseOrderBase):
    """Schema for purchase order response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    status: str
    lines: list[POLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class PurchaseOrderListResponse(BaseModel):
    """Schema for PO list item (without lines)."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    po_number: str
    vendor_id: str
    vendor_name: str
    po_date: date
    total_amount: Decimal
    currency: str
    status: str
    created_at: datetime


# Delivery Note Schemas
class DNLineBase(BaseModel):
    """Base DN line schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    line_number: str
    sku: str | None = None
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal


class DNLineCreate(DNLineBase):
    """Schema for creating DN line."""
    
    pass


class DNLineResponse(DNLineBase):
    """Schema for DN line response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    delivery_note_id: UUID
    accepted_quantity: Decimal
    rejected_quantity: Decimal
    matched_po_line_id: UUID | None = None
    match_score: int | None = None
    status: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class DeliveryNoteBase(BaseModel):
    """Base delivery note schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    dn_number: str
    po_reference: str
    vendor_id: str
    vendor_name: str
    delivery_date: date
    received_date: date | None = None
    subtotal: Decimal = Decimal("0.00")
    currency: str = "USD"
    notes: str | None = None
    source: str = "erp"
    erp_dn_id: str | None = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating delivery note."""
    
    model_config = ConfigDict(from_attributes=True)
    
    lines: list[DNLineCreate] = Field(default_factory=list)


class DeliveryNoteResponse(DeliveryNoteBase):
    """Schema for delivery note response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    status: str
    lines: list[DNLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class DeliveryNoteListResponse(BaseModel):
    """Schema for DN list item (without lines)."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    dn_number: str
    po_reference: str
    vendor_id: str
    vendor_name: str
    delivery_date: date
    subtotal: Decimal
    currency: str
    status: str
    created_at: datetime


# Matching Schemas
class MatchTriggerRequest(BaseModel):
    """Schema for triggering matching."""
    
    model_config = ConfigDict(from_attributes=True)
    
    invoice_id: UUID
    force_rematch: bool = Field(default=False, description="Force rematch even if already matched")
    use_learning: bool = Field(default=True, description="Use learning/cross-ref for matching")


class MatchDecisionResponse(BaseModel):
    """Schema for match decision response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    invoice_id: UUID
    decision: str
    score: int
    confidence: str
    matched_po_id: UUID | None = None
    matched_dn_id: UUID | None = None
    line_matches: list[dict[str, Any]] = Field(default_factory=list)
    exceptions: list[dict[str, Any]] = Field(default_factory=list)
    processing_time_ms: int = 0
    timestamp: datetime


class LineMatchResult(BaseModel):
    """Schema for individual line match result."""
    
    model_config = ConfigDict(from_attributes=True)
    
    invoice_line_id: UUID
    matched_po_line_id: UUID | None = None
    matched_dn_line_id: UUID | None = None
    match_type: str
    score: int
    price_variance_pct: Decimal | None = None
    qty_variance_pct: Decimal | None = None
    status: str


# Exception Schemas
class ExceptionBase(BaseModel):
    """Base exception schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    exception_type: str
    invoice_id: UUID
    invoice_line_id: UUID | None = None
    po_id: UUID | None = None
    po_line_id: UUID | None = None
    dn_id: UUID | None = None
    dn_line_id: UUID | None = None
    message: str
    details: dict[str, Any] | None = None


class ExceptionResponse(ExceptionBase):
    """Schema for exception response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    status: str
    resolved_by: str | None = None
    resolved_at: datetime | None = None
    resolution_notes: str | None = None
    created_at: datetime
    updated_at: datetime


class ExceptionResolveRequest(BaseModel):
    """Schema for resolving exception."""
    
    model_config = ConfigDict(from_attributes=True)
    
    resolution_notes: str
    resolved_by: str
    adjust_amount: Decimal | None = None
    adjust_quantity: Decimal | None = None


class ExceptionDismissRequest(BaseModel):
    """Schema for dismissing exception."""
    
    model_config = ConfigDict(from_attributes=True)
    
    reason: str
    dismissed_by: str


# Balance Ledger Schemas
class BalanceLedgerEntry(BaseModel):
    """Schema for balance ledger entry."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    po_line_id: UUID
    transaction_type: str
    quantity_delta: Decimal
    running_quantity: Decimal
    amount_delta: Decimal
    running_amount: Decimal
    invoice_id: UUID | None = None
    delivery_note_id: UUID | None = None
    description: str | None = None
    reference_number: str | None = None
    created_at: datetime


class BalanceSummary(BaseModel):
    """Schema for PO line balance summary."""
    
    model_config = ConfigDict(from_attributes=True)
    
    po_line_id: UUID
    po_number: str
    line_number: str
    sku: str | None
    description: str
    original_quantity: Decimal
    received_quantity: Decimal
    invoiced_quantity: Decimal
    paid_quantity: Decimal
    remaining_to_receive: Decimal
    remaining_to_invoice: Decimal
    original_amount: Decimal
    invoiced_amount: Decimal
    paid_amount: Decimal
    remaining_amount: Decimal
    entries: list[BalanceLedgerEntry] = Field(default_factory=list)


# Learning Cross-Ref Schemas
class CrossRefBase(BaseModel):
    """Base cross-ref schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    invoice_vendor_id: str
    invoice_sku: str | None = None
    invoice_description: str | None = None
    po_vendor_id: str
    po_sku: str | None = None
    po_description: str | None = None


class CrossRefCreate(CrossRefBase):
    """Schema for creating cross-ref entry."""
    
    pass


class CrossRefResponse(CrossRefBase):
    """Schema for cross-ref response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    match_count: int
    success_count: int
    success_rate: float
    status: str
    confidence: str
    match_type: str
    expires_at: date | None
    is_active: bool
    is_verified: bool
    avg_match_score: float
    created_at: datetime
    updated_at: datetime


class CrossRefConfirmRequest(BaseModel):
    """Schema for confirming a cross-ref match."""
    
    model_config = ConfigDict(from_attributes=True)
    
    cross_ref_id: UUID
    confirmed: bool
    notes: str | None = None

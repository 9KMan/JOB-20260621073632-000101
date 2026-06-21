# api/schemas.py
"""Shared Pydantic schemas for API request/response models."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str = "healthy"
    version: str = "0.1.0"


# Base schemas
class TimestampMixin(BaseModel):
    """Mixin for timestamp fields in responses."""

    created_at: datetime
    updated_at: datetime


class UUIDMixin(BaseModel):
    """Mixin for UUID id field."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID


# Pagination
T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int


class PaginationParams(BaseModel):
    """Pagination query parameters."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        """Calculate offset for query."""
        return (self.page - 1) * self.page_size


# Invoice schemas
class InvoiceLineBase(BaseModel):
    """Base invoice line schema."""

    line_number: int
    description: str
    quantity_invoiced: Decimal
    quantity_unit: str = "EA"
    unit_price: Decimal
    line_amount: Decimal
    tax_rate: Decimal = Field(default=Decimal("0"))
    tax_amount: Decimal = Field(default=Decimal("0"))
    product_code: Optional[str] = None
    purchase_order_line_id: Optional[UUID] = None


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating invoice lines."""

    erp_line_id: Optional[str] = None


class InvoiceLineResponse(InvoiceLineBase, TimestampMixin):
    """Response schema for invoice lines."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    invoice_id: UUID
    line_type: str
    match_score: Optional[float] = None
    erp_line_id: Optional[str] = None


class InvoiceBase(BaseModel):
    """Base invoice schema."""

    vendor_code: str
    vendor_name: str
    vendor_tax_id: Optional[str] = None
    invoice_number: str
    invoice_date: date
    due_date: Optional[date] = None
    currency: str = "USD"
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    purchase_order_id: Optional[UUID] = None
    delivery_note_id: Optional[UUID] = None
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating invoices."""

    erp_invoice_id: Optional[str] = None
    lines: List[InvoiceLineCreate] = Field(default_factory=list)


class InvoiceUpdate(BaseModel):
    """Schema for updating invoices."""

    status: Optional[str] = None
    match_decision: Optional[str] = None
    notes: Optional[str] = None


class InvoiceResponse(InvoiceBase, TimestampMixin):
    """Response schema for invoices."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    amount_paid: Decimal
    match_score: Optional[float] = None
    match_decision: Optional[str] = None
    matched_at: Optional[datetime] = None
    erp_invoice_id: Optional[str] = None
    lines: List[InvoiceLineResponse] = Field(default_factory=list)


class InvoiceListResponse(BaseModel):
    """Response schema for invoice list."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vendor_code: str
    vendor_name: str
    invoice_number: str
    invoice_date: date
    total_amount: Decimal
    status: str
    match_score: Optional[float] = None
    created_at: datetime


# Purchase Order schemas
class PurchaseOrderLineBase(BaseModel):
    """Base PO line schema."""

    line_number: int
    description: str
    quantity_ordered: Decimal
    quantity_unit: str = "EA"
    unit_price: Decimal
    line_amount: Decimal
    tax_rate: Decimal = Field(default=Decimal("0"))
    tax_amount: Decimal = Field(default=Decimal("0"))
    product_code: Optional[str] = None
    product_name: Optional[str] = None


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Schema for creating PO lines."""

    erp_line_id: Optional[str] = None


class PurchaseOrderLineResponse(PurchaseOrderLineBase, TimestampMixin):
    """Response schema for PO lines."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    purchase_order_id: UUID
    line_type: str
    quantity_received: Decimal
    quantity_invoiced: Decimal
    erp_line_id: Optional[str] = None


class PurchaseOrderBase(BaseModel):
    """Base purchase order schema."""

    vendor_code: str
    vendor_name: str
    vendor_tax_id: Optional[str] = None
    po_number: str
    po_date: date
    currency: str = "USD"
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    expected_delivery_date: Optional[date] = None
    delivery_address: Optional[str] = None
    notes: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating purchase orders."""

    erp_po_id: Optional[str] = None
    lines: List[PurchaseOrderLineCreate] = Field(default_factory=list)


class PurchaseOrderResponse(PurchaseOrderBase, TimestampMixin):
    """Response schema for purchase orders."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    erp_po_id: Optional[str] = None
    lines: List[PurchaseOrderLineResponse] = Field(default_factory=list)


class PurchaseOrderListResponse(BaseModel):
    """Response schema for PO list."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vendor_code: str
    vendor_name: str
    po_number: str
    po_date: date
    total_amount: Decimal
    status: str
    created_at: datetime


# Delivery Note schemas
class DeliveryNoteLineBase(BaseModel):
    """Base DN line schema."""

    line_number: int
    description: str
    quantity_delivered: Decimal
    quantity_unit: str = "EA"
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    purchase_order_line_id: Optional[UUID] = None


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating DN lines."""

    erp_line_id: Optional[str] = None


class DeliveryNoteLineResponse(DeliveryNoteLineBase, TimestampMixin):
    """Response schema for DN lines."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    delivery_note_id: UUID
    line_type: str
    quantity_accepted: Decimal
    quantity_rejected: Decimal
    erp_line_id: Optional[str] = None


class DeliveryNoteBase(BaseModel):
    """Base delivery note schema."""

    vendor_code: str
    vendor_name: str
    dn_number: str
    dn_date: date
    received_date: Optional[date] = None
    purchase_order_id: Optional[UUID] = None
    delivery_address: Optional[str] = None
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    notes: Optional[str] = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating delivery notes."""

    erp_dn_id: Optional[str] = None
    lines: List[DeliveryNoteLineCreate] = Field(default_factory=list)


class DeliveryNoteResponse(DeliveryNoteBase, TimestampMixin):
    """Response schema for delivery notes."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    erp_dn_id: Optional[str] = None
    lines: List[DeliveryNoteLineResponse] = Field(default_factory=list)


class DeliveryNoteListResponse(BaseModel):
    """Response schema for DN list."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vendor_code: str
    vendor_name: str
    dn_number: str
    dn_date: date
    status: str
    created_at: datetime


# Matching schemas
class MatchTriggerRequest(BaseModel):
    """Request to trigger matching for an invoice."""

    invoice_id: UUID
    force_rematch: bool = False


class MatchLineResult(BaseModel):
    """Result of matching a single line."""

    invoice_line_id: UUID
    purchase_order_line_id: Optional[UUID] = None
    delivery_note_line_id: Optional[UUID] = None
    match_score: float
    price_variance: Optional[Decimal] = None
    qty_variance: Optional[Decimal] = None
    matched: bool


class MatchResult(BaseModel):
    """Result of matching an invoice."""

    invoice_id: UUID
    overall_score: float
    decision: str
    lines: List[MatchLineResult]
    requires_review: bool = False
    exception_message: Optional[str] = None


class MatchDecisionUpdate(BaseModel):
    """Schema for updating a match decision."""

    invoice_id: UUID
    decision: str
    notes: Optional[str] = None


# Exception schemas
class ExceptionResponse(BaseModel):
    """Response schema for exceptions."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    invoice_id: UUID
    exception_type: str
    exception_message: str
    line_reference: Optional[str] = None
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None


class ExceptionResolveRequest(BaseModel):
    """Request to resolve an exception."""

    resolution: str
    notes: Optional[str] = None


class ExceptionDismissRequest(BaseModel):
    """Request to dismiss an exception."""

    reason: str


# Balance ledger schemas
class BalanceLedgerResponse(BaseModel):
    """Response schema for balance ledger entries."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    purchase_order_id: UUID
    purchase_order_line_id: UUID
    invoice_id: Optional[UUID] = None
    quantity_ordered: Decimal
    quantity_delivered: Decimal
    quantity_invoiced: Decimal
    quantity_matched: Decimal
    balance_quantity: Decimal
    balance_amount: Decimal
    transaction_type: str
    created_at: datetime


class BalanceSummary(BaseModel):
    """Summary of balances for a PO."""

    purchase_order_id: UUID
    po_number: str
    total_ordered: Decimal
    total_invoiced: Decimal
    total_delivered: Decimal
    total_matched: Decimal
    remaining_balance: Decimal
    balance_percentage: float
    lines: List[BalanceLedgerResponse]


# Cross-ref schemas
class CrossRefResponse(BaseModel):
    """Response schema for cross-reference entries."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vendor_code: str
    vendor_name: str
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    unit_price: Decimal
    match_score: float
    use_count: int
    success_rate: float
    is_trusted: bool
    is_promoted: bool
    created_at: datetime


# Error schemas
class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str
    error_code: Optional[str] = None


class ValidationError(BaseModel):
    """Validation error detail."""

    field: str
    message: str


class ValidationErrorResponse(BaseModel):
    """Validation error response."""

    detail: List[ValidationError]

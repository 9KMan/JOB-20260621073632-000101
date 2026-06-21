# api/schemas.py
"""Shared Pydantic schemas for API request/response models.

Provides common schemas used across multiple endpoint groups.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Any, Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

T = TypeVar("T")


# =============================================================================
# Common Schemas
# =============================================================================

class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
    )


class HealthResponse(BaseSchema):
    """Health check response."""
    
    status: str = "healthy"
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    database: str = "connected"


class ErrorDetail(BaseSchema):
    """Error detail schema."""
    
    field: Optional[str] = None
    message: str
    code: Optional[str] = None


class ErrorResponse(BaseSchema):
    """Standard error response."""
    
    error: str
    message: str
    details: Optional[List[ErrorDetail]] = None
    request_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# Pagination Schemas
# =============================================================================

class PaginationParams(BaseModel):
    """Pagination parameters."""
    
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    
    @property
    def offset(self) -> int:
        """Calculate offset for query."""
        return (self.page - 1) * self.page_size


class PaginationMeta(BaseSchema):
    """Pagination metadata."""
    
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool


class PaginatedResponse(BaseSchema, Generic[T]):
    """Generic paginated response."""
    
    items: List[T]
    pagination: PaginationMeta


# =============================================================================
# Invoice Schemas
# =============================================================================

class InvoiceLineBase(BaseSchema):
    """Base invoice line schema."""
    
    line_number: int
    description: str = Field(max_length=500)
    item_number: Optional[str] = None
    vendor_part_number: Optional[str] = None
    quantity_invoiced: Decimal = Field(ge=0)
    quantity_unit: str = "EA"
    unit_price: Decimal = Field(ge=0)
    line_amount: Decimal = Field(ge=0)
    tax_rate: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    gl_account: Optional[str] = None
    department_code: Optional[str] = None
    cost_center: Optional[str] = None


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating invoice line."""
    
    po_line_id: Optional[UUID] = None
    delivery_line_id: Optional[UUID] = None


class InvoiceLineResponse(InvoiceLineBase):
    """Schema for invoice line response."""
    
    id: UUID
    invoice_id: UUID
    status: str
    po_line_id: Optional[UUID] = None
    delivery_line_id: Optional[UUID] = None
    matched_quantity: Optional[Decimal] = None
    match_score: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime


class InvoiceBase(BaseSchema):
    """Base invoice schema."""
    
    vendor_number: str = Field(max_length=50)
    vendor_name: str = Field(max_length=255)
    invoice_number: str = Field(max_length=100)
    invoice_date: date
    due_date: Optional[date] = None
    received_date: date
    subtotal: Decimal = Field(ge=0)
    tax_amount: Decimal = Field(ge=0, default=Decimal("0.00"))
    total_amount: Decimal = Field(ge=0)
    currency_code: str = Field(default="USD", max_length=3)
    payment_terms: Optional[str] = None
    gl_account: Optional[str] = None
    department_code: Optional[str] = None
    cost_center: Optional[str] = None
    source_system: str = Field(default="manual", max_length=50)
    source_reference: Optional[str] = None
    notes: Optional[str] = None
    internal_comments: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating invoice."""
    
    lines: List[InvoiceLineCreate]


class InvoiceUpdate(BaseSchema):
    """Schema for updating invoice."""
    
    vendor_number: Optional[str] = None
    vendor_name: Optional[str] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    subtotal: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    internal_comments: Optional[str] = None


class InvoiceResponse(InvoiceBase):
    """Schema for invoice response."""
    
    id: UUID
    status: str
    matched_po_id: Optional[UUID] = None
    matched_delivery_id: Optional[UUID] = None
    match_score: Optional[Decimal] = None
    match_decision: Optional[str] = None
    match_decision_at: Optional[datetime] = None
    match_decided_by: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    lines: List[InvoiceLineResponse] = []


class InvoiceListResponse(BaseSchema):
    """Schema for invoice list item (without lines)."""
    
    id: UUID
    vendor_number: str
    vendor_name: str
    invoice_number: str
    invoice_date: date
    total_amount: Decimal
    currency_code: str
    status: str
    match_score: Optional[Decimal] = None
    match_decision: Optional[str] = None
    created_at: datetime


# =============================================================================
# Purchase Order Schemas
# =============================================================================

class PurchaseOrderLineBase(BaseSchema):
    """Base PO line schema."""
    
    line_number: int
    description: str = Field(max_length=500)
    item_number: Optional[str] = None
    vendor_part_number: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    quantity_ordered: Decimal = Field(ge=0)
    quantity_unit: str = "EA"
    unit_price: Decimal = Field(ge=0)
    line_amount: Decimal = Field(ge=0)
    gl_account: Optional[str] = None
    department_code: Optional[str] = None
    cost_center: Optional[str] = None
    promised_delivery_date: Optional[date] = None


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Schema for creating PO line."""
    pass


class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    """Schema for PO line response."""
    
    id: UUID
    po_id: UUID
    quantity_delivered: Decimal
    quantity_invoiced: Decimal
    status: str
    created_at: datetime
    updated_at: datetime


class PurchaseOrderBase(BaseSchema):
    """Base PO schema."""
    
    vendor_number: str = Field(max_length=50)
    vendor_name: str = Field(max_length=255)
    po_number: str = Field(max_length=100)
    po_date: date
    expected_delivery_date: Optional[date] = None
    subtotal: Decimal = Field(ge=0)
    tax_amount: Decimal = Field(ge=0, default=Decimal("0.00"))
    total_amount: Decimal = Field(ge=0)
    currency_code: str = Field(default="USD", max_length=3)
    buyer_name: Optional[str] = None
    approver_name: Optional[str] = None
    approved_date: Optional[date] = None
    ship_to_location: Optional[str] = None
    payment_terms: Optional[str] = None
    source_system: str = Field(default="erp", max_length=50)
    source_reference: Optional[str] = None
    notes: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating PO."""
    
    lines: List[PurchaseOrderLineCreate]


class PurchaseOrderResponse(PurchaseOrderBase):
    """Schema for PO response."""
    
    id: UUID
    status: str
    closed_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    lines: List[PurchaseOrderLineResponse] = []


class PurchaseOrderListResponse(BaseSchema):
    """Schema for PO list item (without lines)."""
    
    id: UUID
    vendor_number: str
    vendor_name: str
    po_number: str
    po_date: date
    total_amount: Decimal
    currency_code: str
    status: str
    created_at: datetime


# =============================================================================
# Delivery Note Schemas
# =============================================================================

class DeliveryNoteLineBase(BaseSchema):
    """Base DN line schema."""
    
    line_number: int
    description: str = Field(max_length=500)
    item_number: Optional[str] = None
    vendor_part_number: Optional[str] = None
    quantity_delivered: Decimal = Field(ge=0)
    quantity_unit: str = "EA"
    quantity_accepted: Decimal = Field(ge=0)
    quantity_rejected: Decimal = Field(ge=0)
    unit_price: Optional[Decimal] = None
    line_amount: Optional[Decimal] = None
    acceptance_notes: Optional[str] = None


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating DN line."""
    
    po_line_id: Optional[UUID] = None


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """Schema for DN line response."""
    
    id: UUID
    dn_id: UUID
    po_line_id: Optional[UUID] = None
    status: str
    quantity_invoiced: Decimal
    created_at: datetime
    updated_at: datetime


class DeliveryNoteBase(BaseSchema):
    """Base DN schema."""
    
    vendor_number: str = Field(max_length=50)
    vendor_name: str = Field(max_length=255)
    dn_number: str = Field(max_length=100)
    carrier_name: Optional[str] = None
    tracking_number: Optional[str] = None
    po_id: Optional[UUID] = None
    dn_date: date
    received_date: date
    subtotal: Decimal = Field(ge=0)
    tax_amount: Decimal = Field(ge=0, default=Decimal("0.00"))
    total_amount: Decimal = Field(ge=0)
    currency_code: str = Field(default="USD", max_length=3)
    ship_to_location: Optional[str] = None
    received_by: Optional[str] = None
    source_system: str = Field(default="warehouse", max_length=50)
    source_reference: Optional[str] = None
    notes: Optional[str] = None
    condition_notes: Optional[str] = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating DN."""
    
    lines: List[DeliveryNoteLineCreate]


class DeliveryNoteResponse(DeliveryNoteBase):
    """Schema for DN response."""
    
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    lines: List[DeliveryNoteLineResponse] = []


class DeliveryNoteListResponse(BaseSchema):
    """Schema for DN list item (without lines)."""
    
    id: UUID
    vendor_number: str
    vendor_name: str
    dn_number: str
    dn_date: date
    total_amount: Decimal
    currency_code: str
    status: str
    po_id: Optional[UUID] = None
    created_at: datetime


# =============================================================================
# Matching Schemas
# =============================================================================

class MatchRequest(BaseSchema):
    """Request to trigger matching for an invoice."""
    
    invoice_id: UUID
    force_rematch: bool = False


class MatchDecisionRequest(BaseSchema):
    """Request to record a match decision."""
    
    invoice_id: UUID
    decision: str = Field(..., description="auto_approved, manual_approved, exception, rejected, dismissed")
    notes: Optional[str] = None


class MatchScoreDetail(BaseSchema):
    """Detailed breakdown of match score."""
    
    price_score: Decimal
    quantity_score: Decimal
    vendor_score: Decimal
    date_score: Decimal
    learned_score: Decimal = Decimal("0")
    total_score: Decimal


class MatchResult(BaseSchema):
    """Result of a match operation."""
    
    invoice_id: UUID
    match_status: str
    match_score: Optional[Decimal] = None
    decision: Optional[str] = None
    matched_po_id: Optional[UUID] = None
    matched_delivery_id: Optional[UUID] = None
    score_details: Optional[MatchScoreDetail] = None
    message: str


class MatchHistoryItem(BaseSchema):
    """Historical match record."""
    
    id: UUID
    invoice_id: UUID
    po_id: UUID
    delivery_id: Optional[UUID] = None
    score: Decimal
    decision: str
    decided_at: datetime
    decided_by: Optional[str] = None


# =============================================================================
# Exception Schemas
# =============================================================================

class ExceptionBase(BaseSchema):
    """Base exception schema."""
    
    invoice_id: UUID
    exception_type: str
    message: str
    po_id: Optional[UUID] = None
    po_line_id: Optional[UUID] = None
    delivery_id: Optional[UUID] = None
    price_variance: Optional[Decimal] = None
    quantity_variance: Optional[Decimal] = None


class ExceptionResponse(ExceptionBase):
    """Exception response schema."""
    
    id: UUID
    status: str
    resolution: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ExceptionResolveRequest(BaseSchema):
    """Request to resolve an exception."""
    
    resolution: str = Field(..., description="approved_with_variance, manual_match, write_off, held_for_review, escalated, dismissed")
    notes: Optional[str] = None


# =============================================================================
# Balance Ledger Schemas
# =============================================================================

class BalanceLedgerEntry(BaseSchema):
    """Balance ledger entry response."""
    
    id: UUID
    po_line_id: UUID
    entry_type: str
    entry_number: str
    reference_type: str
    reference_id: UUID
    entry_date: date
    quantity: Optional[Decimal] = None
    amount: Optional[Decimal] = None
    balance_quantity: Optional[Decimal] = None
    balance_amount: Optional[Decimal] = None
    total_ordered_quantity: Decimal
    total_delivered_quantity: Decimal
    total_invoiced_quantity: Decimal
    total_invoiced_amount: Decimal
    notes: Optional[str] = None
    created_at: datetime


class BalanceSummary(BaseSchema):
    """Summary of balances for a PO line."""
    
    po_line_id: UUID
    total_ordered: Decimal
    total_delivered: Decimal
    total_invoiced: Decimal
    remaining_to_deliver: Decimal
    remaining_to_invoice: Decimal
    balance_value: Decimal
    entries: List[BalanceLedgerEntry] = []


# =============================================================================
# Learning/CrossRef Schemas
# =============================================================================

class CrossRefResponse(BaseSchema):
    """Cross reference response."""
    
    id: UUID
    vendor_number: str
    vendor_name: str
    item_number: Optional[str] = None
    vendor_item_number: Optional[str] = None
    po_line_id: Optional[UUID] = None
    unit_price: Decimal
    price_tolerance_percent: Decimal
    typical_quantity: Optional[Decimal] = None
    quantity_tolerance_percent: Decimal
    confidence: str
    match_count: int
    confirm_count: int
    reject_count: int
    is_promoted: bool
    promoted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class CrossRefPromoteRequest(BaseSchema):
    """Request to promote a cross reference."""
    
    cross_ref_id: UUID
    reason: str

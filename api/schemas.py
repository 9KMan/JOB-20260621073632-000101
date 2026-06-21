// api/schemas.py
"""Shared Pydantic schemas for API request/response validation.

All schemas are organized by domain and use standard naming conventions.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any, Generic, TypeVar

from pydantic import BaseModel, Field, field_validator, computed_field

# Generic type for list responses
T = TypeVar("T")


# =============================================================================
# Common / Shared Schemas
# =============================================================================


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(description="Service health status")
    version: str = Field(description="Application version")
    database: str = Field(description="Database connection status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(description="Error type")
    message: str = Field(description="Human-readable error message")
    details: dict[str, Any] | None = Field(
        default=None,
        description="Additional error details",
    )
    request_id: str | None = Field(
        default=None,
        description="Request tracking ID",
    )


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""

    page: Annotated[int, Field(ge=1, default=1, description="Page number")]
    page_size: Annotated[
        int,
        Field(ge=1, le=100, default=20, description="Items per page"),
    ]

    @computed_field
    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated list response."""

    items: list[T] = Field(description="List of items")
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Items per page")
    pages: int = Field(description="Total number of pages")

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        """Create paginated response with calculated pages."""
        pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )


# =============================================================================
# Invoice Schemas
# =============================================================================


class InvoiceLineCreate(BaseModel):
    """Schema for creating an invoice line item."""

    line_number: int = Field(description="Line item sequence number")
    description: str | None = Field(default=None, max_length=500)
    sku: str | None = Field(default=None, max_length=100)
    product_code: str | None = Field(default=None, max_length=100)
    barcode: str | None = Field(default=None, max_length=50)
    quantity: Annotated[Decimal, Field(gt=0)] = Field(
        description="Invoiced quantity"
    )
    unit_of_measure: str | None = Field(default=None, max_length=20)
    unit_price: Annotated[Decimal, Field(ge=0)] = Field(
        description="Price per unit"
    )
    line_total: Annotated[Decimal, Field(ge=0)] = Field(
        description="Total line amount"
    )
    tax_amount: Decimal | None = Field(default=None, ge=0)


class InvoiceLineResponse(InvoiceLineCreate):
    """Response schema for invoice line item."""

    id: uuid.UUID
    invoice_id: uuid.UUID
    po_line_id: uuid.UUID | None = None
    dn_line_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime


class InvoiceCreate(BaseModel):
    """Schema for creating a new invoice."""

    vendor_id: str = Field(max_length=100)
    vendor_name: str | None = Field(default=None, max_length=255)
    vendor_tax_id: str | None = Field(default=None, max_length=50)
    invoice_number: str = Field(max_length=100)
    invoice_date: str = Field(max_length=10)
    due_date: str | None = Field(default=None, max_length=10)
    currency: str = Field(default="USD", max_length=3)
    subtotal: Decimal = Field(ge=0)
    tax_amount: Decimal = Field(ge=0, default=Decimal("0.00"))
    total_amount: Decimal = Field(ge=0)
    tax_rate: Decimal | None = Field(default=None, ge=0)
    payment_terms: str | None = Field(default=None, max_length=50)
    notes: str | None = Field(default=None)
    is_credit_memo: bool = Field(default=False)
    lines: list[InvoiceLineCreate] = Field(default_factory=list)

    @field_validator("invoice_date", "due_date", mode="before")
    @classmethod
    def validate_date_format(cls, v: str | None) -> str | None:
        """Validate date is in YYYY-MM-DD format."""
        if v is None:
            return v
        # Basic validation - in production, use proper date parsing
        if len(v) != 10 or v[4] != "-" or v[7] != "-":
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v


class InvoiceUpdate(BaseModel):
    """Schema for updating an invoice."""

    vendor_name: str | None = Field(default=None, max_length=255)
    due_date: str | None = Field(default=None, max_length=10)
    status: str | None = None
    payment_terms: str | None = Field(default=None, max_length=50)
    notes: str | None = None


class InvoiceResponse(BaseModel):
    """Response schema for invoice."""

    id: uuid.UUID
    vendor_id: str
    vendor_name: str | None
    vendor_tax_id: str | None
    invoice_number: str
    invoice_date: str
    due_date: str | None
    currency: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    tax_rate: Decimal | None
    status: str
    matching_decision: str | None
    match_score: float | None
    payment_terms: str | None
    notes: str | None
    is_credit_memo: bool
    matched_po_id: uuid.UUID | None
    matched_dn_id: uuid.UUID | None
    lines: list[InvoiceLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InvoiceListResponse(PaginatedResponse[InvoiceResponse]):
    """Paginated list of invoices."""
    pass


# =============================================================================
# Purchase Order Schemas
# =============================================================================


class PurchaseOrderLineCreate(BaseModel):
    """Schema for creating a PO line item."""

    line_number: int
    description: str | None = Field(default=None, max_length=500)
    sku: str | None = Field(default=None, max_length=100)
    product_code: str | None = Field(default=None, max_length=100)
    manufacturer_part: str | None = Field(default=None, max_length=100)
    quantity_ordered: Annotated[Decimal, Field(gt=0)]
    quantity_received: Decimal = Field(default=Decimal("0"), ge=0)
    quantity_invoiced: Decimal = Field(default=Decimal("0"), ge=0)
    unit_of_measure: str | None = Field(default=None, max_length=20)
    unit_price: Annotated[Decimal, Field(ge=0)]
    line_total: Annotated[Decimal, Field(ge=0)]
    tax_amount: Decimal | None = Field(default=None, ge=0)
    required_date: str | None = Field(default=None, max_length=10)
    promised_date: str | None = Field(default=None, max_length=10)


class PurchaseOrderLineResponse(PurchaseOrderLineCreate):
    """Response schema for PO line item."""

    id: uuid.UUID
    purchase_order_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class PurchaseOrderCreate(BaseModel):
    """Schema for creating a new purchase order."""

    vendor_id: str = Field(max_length=100)
    vendor_name: str | None = Field(default=None, max_length=255)
    vendor_address: str | None = None
    po_number: str = Field(max_length=100)
    po_date: str = Field(max_length=10)
    required_date: str | None = Field(default=None, max_length=10)
    currency: str = Field(default="USD", max_length=3)
    subtotal: Decimal = Field(ge=0)
    tax_amount: Decimal = Field(ge=0, default=Decimal("0.00"))
    total_amount: Decimal = Field(ge=0)
    status: str = Field(default="approved")
    buyer_name: str | None = Field(default=None, max_length=100)
    department: str | None = Field(default=None, max_length=100)
    project_code: str | None = Field(default=None, max_length=50)
    notes: str | None = None
    terms: str | None = Field(default=None, max_length=100)
    lines: list[PurchaseOrderLineCreate] = Field(default_factory=list)


class PurchaseOrderResponse(BaseModel):
    """Response schema for purchase order."""

    id: uuid.UUID
    vendor_id: str
    vendor_name: str | None
    vendor_address: str | None
    po_number: str
    po_date: str
    required_date: str | None
    currency: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    status: str
    buyer_name: str | None
    department: str | None
    project_code: str | None
    notes: str | None
    terms: str | None
    lines: list[PurchaseOrderLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PurchaseOrderListResponse(PaginatedResponse[PurchaseOrderResponse]):
    """Paginated list of purchase orders."""
    pass


# =============================================================================
# Delivery Note Schemas
# =============================================================================


class DeliveryNoteLineCreate(BaseModel):
    """Schema for creating a delivery note line item."""

    line_number: int
    description: str | None = Field(default=None, max_length=500)
    sku: str | None = Field(default=None, max_length=100)
    product_code: str | None = Field(default=None, max_length=100)
    barcode: str | None = Field(default=None, max_length=50)
    quantity_delivered: Annotated[Decimal, Field(gt=0)]
    quantity_accepted: Decimal | None = Field(default=None, ge=0)
    quantity_rejected: Decimal | None = Field(default=None, ge=0)
    unit_of_measure: str | None = Field(default=None, max_length=20)
    po_line_id: uuid.UUID | None = None
    batch_number: str | None = Field(default=None, max_length=100)
    serial_number: str | None = Field(default=None, max_length=100)
    expiry_date: str | None = Field(default=None, max_length=10)


class DeliveryNoteLineResponse(DeliveryNoteLineCreate):
    """Response schema for delivery note line item."""

    id: uuid.UUID
    delivery_note_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class DeliveryNoteCreate(BaseModel):
    """Schema for creating a new delivery note."""

    vendor_id: str = Field(max_length=100)
    vendor_name: str | None = Field(default=None, max_length=255)
    dn_number: str = Field(max_length=100)
    po_number: str | None = Field(default=None, max_length=100)
    delivery_date: str = Field(max_length=10)
    received_date: str | None = Field(default=None, max_length=10)
    reference_number: str | None = Field(default=None, max_length=100)
    carrier: str | None = Field(default=None, max_length=100)
    tracking_number: str | None = Field(default=None, max_length=100)
    currency: str = Field(default="USD", max_length=3)
    total_amount: Decimal = Field(ge=0)
    status: str = Field(default="confirmed")
    source: str = Field(default="erp")
    ocr_confidence: float | None = Field(default=None, ge=0, le=100)
    notes: str | None = None
    lines: list[DeliveryNoteLineCreate] = Field(default_factory=list)


class DeliveryNoteResponse(BaseModel):
    """Response schema for delivery note."""

    id: uuid.UUID
    vendor_id: str
    vendor_name: str | None
    dn_number: str
    po_number: str | None
    delivery_date: str
    received_date: str | None
    reference_number: str | None
    carrier: str | None
    tracking_number: str | None
    currency: str
    total_amount: Decimal
    status: str
    source: str
    ocr_confidence: float | None
    notes: str | None
    po_reference_id: uuid.UUID | None
    lines: list[DeliveryNoteLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DeliveryNoteListResponse(PaginatedResponse[DeliveryNoteResponse]):
    """Paginated list of delivery notes."""
    pass


# =============================================================================
# Matching Schemas
# =============================================================================


class MatchingRequest(BaseModel):
    """Request to trigger matching for an invoice."""

    invoice_id: uuid.UUID = Field(description="Invoice ID to match")
    force_rematch: bool = Field(
        default=False,
        description="Force re-matching even if already matched",
    )


class MatchingResultItem(BaseModel):
    """Individual line matching result."""

    invoice_line_id: uuid.UUID
    po_line_id: uuid.UUID | None
    dn_line_id: uuid.UUID | None
    match_score: float
    match_type: str
    price_variance: Decimal | None
    quantity_variance: Decimal | None
    confidence: str


class MatchingResponse(BaseModel):
    """Response from matching operation."""

    invoice_id: uuid.UUID
    decision: str
    overall_score: float
    line_results: list[MatchingResultItem] = Field(default_factory=list)
    processing_time_ms: int
    match_type: str
    exceptions: list[str] = Field(default_factory=list)


class MatchingDecisionResponse(BaseModel):
    """Detailed matching decision information."""

    invoice_id: uuid.UUID
    decision: str
    decision_label: str
    overall_score: float
    threshold_applied: str
    matched_po_id: uuid.UUID | None
    matched_dn_id: uuid.UUID | None
    line_matches: int
    total_lines: int
    price_variance_pct: float | None
    quantity_variance_pct: float | None
    requires_review: bool
    exception_ids: list[uuid.UUID] = Field(default_factory=list)


# =============================================================================
# Exception Schemas
# =============================================================================


class ExceptionCreate(BaseModel):
    """Schema for creating an exception (usually auto-generated)."""

    invoice_id: uuid.UUID
    exception_type: str
    po_id: uuid.UUID | None = None
    dn_id: uuid.UUID | None = None
    severity: str = Field(default="medium")
    description: str | None = None
    po_line_id: uuid.UUID | None = None
    amount_variance: Decimal | None = None
    quantity_variance: Decimal | None = None


class ExceptionResponse(BaseModel):
    """Response schema for exception."""

    id: uuid.UUID
    invoice_id: uuid.UUID
    exception_type: str
    status: str
    severity: str
    description: str | None
    po_id: uuid.UUID | None
    dn_id: uuid.UUID | None
    po_line_id: uuid.UUID | None
    amount_variance: Decimal | None
    quantity_variance: Decimal | None
    resolution_notes: str | None
    resolved_by: str | None
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExceptionListResponse(PaginatedResponse[ExceptionResponse]):
    """Paginated list of exceptions."""
    pass


class ExceptionResolution(BaseModel):
    """Schema for resolving an exception."""

    resolution_notes: str = Field(max_length=1000)
    resolved_by: str = Field(max_length=100)
    action: str = Field(
        description="Resolution action: approve, reject, adjust, dismiss"
    )
    adjusted_amount: Decimal | None = Field(default=None)


# =============================================================================
# Balance Ledger Schemas
# =============================================================================


class BalanceLedgerResponse(BaseModel):
    """Response schema for balance ledger entry."""

    id: uuid.UUID
    po_line_id: uuid.UUID
    po_id: uuid.UUID
    po_number: str
    vendor_id: str
    po_quantity_ordered: Decimal
    po_quantity_received: Decimal
    po_unit_price: Decimal
    invoice_quantity: Decimal | None
    invoice_unit_price: Decimal | None
    invoice_amount: Decimal | None
    balance_quantity: Decimal
    balance_amount: Decimal
    paid_quantity: Decimal
    paid_amount: Decimal
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# Cross Ref / Learning Schemas
# =============================================================================


class CrossRefResponse(BaseModel):
    """Response schema for cross reference entry."""

    id: uuid.UUID
    invoice_id: uuid.UUID
    invoice_line_id: uuid.UUID | None
    invoice_number: str
    invoice_date: str
    invoice_quantity: Decimal | None
    invoice_unit_price: Decimal | None
    po_id: uuid.UUID | None
    po_line_id: uuid.UUID | None
    po_number: str | None
    po_date: str | None
    po_quantity: Decimal | None
    po_unit_price: Decimal | None
    dn_id: uuid.UUID | None
    dn_line_id: uuid.UUID | None
    dn_number: str | None
    dn_quantity: Decimal | None
    sku: str | None
    sku_match_type: str | None
    description: str | None
    vendor_id: str
    match_type: str
    confidence: str
    match_score: float
    price_variance: Decimal | None
    price_variance_pct: float | None
    quantity_variance: Decimal | None
    quantity_variance_pct: float | None
    verified: bool
    verified_by: str | None
    verified_at: str | None
    source: str
    exception_type: str | None
    notes: str | None
    usage_count: int
    last_used_at: str | None
    success_rate: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CrossRefListResponse(PaginatedResponse[CrossRefResponse]):
    """Paginated list of cross reference entries."""
    pass

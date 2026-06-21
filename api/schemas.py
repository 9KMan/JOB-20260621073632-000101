# api/schemas.py
"""Shared Pydantic request/response models for API endpoints."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

T = TypeVar("T")


# ============== Base Schemas ==============

class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
    )


# ============== Common Schemas ==============

class HealthCheckResponse(BaseSchema):
    """Health check response."""

    status: str = "healthy"
    version: str
    timestamp: datetime


class ErrorResponse(BaseSchema):
    """Standard error response."""

    error: str
    message: str
    details: dict[str, Any] | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuccessResponse(BaseSchema):
    """Standard success response."""

    success: bool = True
    message: str
    data: dict[str, Any] | None = None


# ============== Pagination ==============

class PaginationParams(BaseModel):
    """Pagination parameters."""

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @field_validator("page")
    @classmethod
    def validate_page(cls, v: int) -> int:
        """Validate page number."""
        return max(1, v)

    @field_validator("page_size")
    @classmethod
    def validate_page_size(cls, v: int) -> int:
        """Validate page size."""
        return min(max(1, v), 100)

    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseSchema, Generic[T]):
    """Generic paginated response."""

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    @field_validator("total_pages", mode="before")
    @classmethod
    def calculate_total_pages(cls, v: Any, info: Any) -> int:
        """Calculate total pages."""
        if isinstance(v, int):
            return v
        return 1


# ============== Invoice Schemas ==============

class InvoiceLineBase(BaseSchema):
    """Base invoice line schema."""

    line_number: int
    description: str
    sku: str | None = None
    product_code: str | None = None
    quantity: Decimal
    unit_of_measure: str = "EA"
    unit_price: Decimal
    line_amount: Decimal
    tax_code: str | None = None
    tax_rate: Decimal = Field(default=Decimal("0"))
    po_line_id: str | None = None


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating invoice line."""

    supplier_part_number: str | None = None


class InvoiceLineResponse(InvoiceLineBase):
    """Invoice line response schema."""

    id: str
    invoice_id: str
    quantity_received: Decimal = Field(default=Decimal("0"))
    matched_quantity: Decimal = Field(default=Decimal("0"))
    is_matched: bool = False
    is_exception: bool = False
    exception_reason: str | None = None
    created_at: datetime
    updated_at: datetime


class InvoiceBase(BaseSchema):
    """Base invoice schema."""

    vendor_id: str
    vendor_name: str
    vendor_tax_id: str | None = None
    invoice_number: str
    invoice_date: date
    due_date: date | None = None
    subtotal: Decimal
    tax_amount: Decimal = Field(default=Decimal("0"))
    total_amount: Decimal
    currency: str = "USD"


class InvoiceCreate(InvoiceBase):
    """Schema for creating invoice."""

    lines: list[InvoiceLineCreate]
    external_id: str | None = None
    erp_reference: str | None = None
    metadata: dict[str, Any] | None = None
    notes: str | None = None


class InvoiceUpdate(BaseSchema):
    """Schema for updating invoice."""

    status: str | None = None
    notes: str | None = None
    metadata: dict[str, Any] | None = None


class InvoiceResponse(InvoiceBase):
    """Invoice response schema."""

    id: str
    status: str
    matched_po_id: str | None = None
    match_decision: str | None = None
    match_score: float | None = None
    match_confidence: str | None = None
    match_reason: str | None = None
    has_exception: bool = False
    exception_types: list[str] | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    external_id: str | None = None
    erp_reference: str | None = None
    payment_reference: str | None = None
    lines: list[InvoiceLineResponse] = []
    created_at: datetime
    updated_at: datetime


class InvoiceListResponse(PaginatedResponse[InvoiceResponse]):
    """Paginated invoice list response."""

    pass


# ============== Purchase Order Schemas ==============

class POLineBase(BaseSchema):
    """Base PO line schema."""

    line_number: int
    description: str
    sku: str | None = None
    product_code: str | None = None
    quantity_ordered: Decimal
    unit_of_measure: str = "EA"
    unit_price: Decimal
    line_amount: Decimal
    tax_code: str | None = None
    tax_rate: Decimal = Field(default=Decimal("0"))
    delivery_date: date | None = None


class POLineCreate(POLineBase):
    """Schema for creating PO line."""

    supplier_part_number: str | None = None
    manufacturer: str | None = None


class POLineResponse(POLineBase):
    """PO line response schema."""

    id: str
    po_id: str
    quantity_delivered: Decimal = Field(default=Decimal("0"))
    quantity_invoiced: Decimal = Field(default=Decimal("0"))
    quantity_accepted: Decimal = Field(default=Decimal("0"))
    is_closed: bool = False
    closed_at: datetime | None = None
    close_reason: str | None = None
    created_at: datetime
    updated_at: datetime


class PurchaseOrderBase(BaseSchema):
    """Base purchase order schema."""

    vendor_id: str
    vendor_name: str
    vendor_address: str | None = None
    po_number: str
    po_date: date
    delivery_date: date | None = None
    subtotal: Decimal
    tax_amount: Decimal = Field(default=Decimal("0"))
    total_amount: Decimal
    currency: str = "USD"


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating purchase order."""

    lines: list[POLineCreate]
    external_id: str | None = None
    erp_reference: str | None = None
    buyer_name: str | None = None
    department: str | None = None
    payment_terms: str | None = None
    shipping_terms: str | None = None
    metadata: dict[str, Any] | None = None
    notes: str | None = None


class PurchaseOrderResponse(PurchaseOrderBase):
    """Purchase order response schema."""

    id: str
    status: str
    is_closed: bool = False
    closed_at: datetime | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    external_id: str | None = None
    erp_reference: str | None = None
    buyer_name: str | None = None
    department: str | None = None
    payment_terms: str | None = None
    shipping_terms: str | None = None
    lines: list[POLineResponse] = []
    created_at: datetime
    updated_at: datetime


class PurchaseOrderListResponse(PaginatedResponse[PurchaseOrderResponse]):
    """Paginated PO list response."""

    pass


# ============== Delivery Note Schemas ==============

class DNLineBase(BaseSchema):
    """Base delivery note line schema."""

    line_number: int
    description: str
    sku: str | None = None
    product_code: str | None = None
    quantity_delivered: Decimal
    unit_of_measure: str = "EA"
    po_line_id: str | None = None


class DNLineCreate(DNLineBase):
    """Schema for creating delivery note line."""

    supplier_part_number: str | None = None
    unit_price: Decimal | None = None


class DNLineResponse(DNLineBase):
    """Delivery note line response schema."""

    id: str
    dn_id: str
    quantity_accepted: Decimal = Field(default=Decimal("0"))
    quantity_rejected: Decimal = Field(default=Decimal("0"))
    is_accepted: bool = False
    is_exception: bool = False
    exception_reason: str | None = None
    unit_price: Decimal | None = None
    line_amount: Decimal = Field(default=Decimal("0"))
    created_at: datetime
    updated_at: datetime


class DeliveryNoteBase(BaseSchema):
    """Base delivery note schema."""

    vendor_id: str
    vendor_name: str
    po_id: str | None = None
    po_number: str | None = None
    dn_number: str
    delivery_date: date
    received_date: date | None = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating delivery note."""

    lines: list[DNLineCreate]
    external_id: str | None = None
    erp_reference: str | None = None
    received_by: str | None = None
    receiving_location: str | None = None
    metadata: dict[str, Any] | None = None
    notes: str | None = None


class DeliveryNoteResponse(DeliveryNoteBase):
    """Delivery note response schema."""

    id: str
    status: str
    total_amount: Decimal = Field(default=Decimal("0"))
    currency: str = "USD"
    external_id: str | None = None
    erp_reference: str | None = None
    received_by: str | None = None
    receiving_location: str | None = None
    lines: list[DNLineResponse] = []
    created_at: datetime
    updated_at: datetime


class DeliveryNoteListResponse(PaginatedResponse[DeliveryNoteResponse]):
    """Paginated DN list response."""

    pass


# ============== Matching Schemas ==============

class MatchTriggerRequest(BaseSchema):
    """Request to trigger matching for an invoice."""

    invoice_id: str
    match_type: str = Field(
        default="full",
        description="Match type: 'full', 'partial', or 'revalidate'",
    )


class MatchResultLine(BaseSchema):
    """Matched line result."""

    invoice_line_id: str
    po_line_id: str | None = None
    dn_line_id: str | None = None
    matched_quantity: Decimal
    match_score: float
    match_confidence: str
    price_variance: Decimal = Field(default=Decimal("0"))
    quantity_variance: Decimal = Field(default=Decimal("0"))
    match_reason: str


class MatchResult(BaseSchema):
    """Matching result."""

    invoice_id: str
    decision: str
    overall_score: float
    confidence: str
    matched_lines: list[MatchResultLine]
    unmatched_lines: list[str] = []
    exceptions: list[str] = []
    reason: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MatchDecisionRequest(BaseSchema):
    """Request to make a matching decision."""

    invoice_id: str
    decision: str = Field(
        description="Decision: 'approve', 'reject', 'exception', 'no_match'",
    )
    notes: str | None = None
    user_id: str | None = None


# ============== Exception Schemas ==============

class ExceptionResponse(BaseSchema):
    """Exception response schema."""

    id: str
    invoice_id: str
    exception_type: str
    status: str
    description: str | None = None
    invoice_number: str | None = None
    po_number: str | None = None
    vendor_id: str | None = None
    vendor_name: str | None = None
    amount: Decimal | None = None
    quantity_variance: Decimal | None = None
    price_variance: Decimal | None = None
    created_at: datetime
    updated_at: datetime


class ExceptionListResponse(PaginatedResponse[ExceptionResponse]):
    """Paginated exception list response."""

    pass


class ExceptionResolveRequest(BaseSchema):
    """Request to resolve an exception."""

    invoice_id: str
    resolution: str = Field(
        description="Resolution: 'approve', 'reject', 'adjust', 'write_off'",
    )
    notes: str | None = None
    user_id: str | None = None


class ExceptionDismissRequest(BaseSchema):
    """Request to dismiss an exception."""

    invoice_id: str
    reason: str
    user_id: str | None = None


# ============== Balance Ledger Schemas ==============

class BalanceLedgerEntry(BaseSchema):
    """Balance ledger entry."""

    id: str
    po_line_id: str
    po_id: str
    vendor_id: str
    invoice_id: str | None = None
    transaction_type: str
    transaction_date: date
    reference_number: str | None = None
    quantity: Decimal
    running_quantity: Decimal
    amount: Decimal
    running_amount: Decimal
    balance_date: date
    currency: str
    is_reconciled: bool
    created_at: datetime


class BalanceResponse(BaseSchema):
    """Balance response for a PO line."""

    po_line_id: str
    po_id: str
    vendor_id: str
    quantity_ordered: Decimal
    quantity_delivered: Decimal
    quantity_invoiced: Decimal
    quantity_accepted: Decimal
    open_quantity: Decimal
    open_amount: Decimal
    currency: str
    transactions: list[BalanceLedgerEntry] = []


# ============== Cross Ref (Learning) Schemas ==============

class CrossRefResponse(BaseSchema):
    """Cross reference (learning) entry response."""

    id: str
    vendor_id: str
    vendor_name: str | None = None
    sku: str | None = None
    product_code: str | None = None
    supplier_part_number: str | None = None
    po_number: str | None = None
    invoice_number: str | None = None
    match_count: int
    confidence_score: float
    is_active: bool
    is_promoted: bool
    last_matched_at: datetime
    created_at: datetime


class CrossRefListResponse(PaginatedResponse[CrossRefResponse]):
    """Paginated cross ref list response."""

    pass

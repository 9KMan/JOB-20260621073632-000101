# api/schemas.py
"""Shared Pydantic schemas for API request/response models.

Contains base schemas and common patterns used across endpoints.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Generic type for paginated responses
T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base Pydantic schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
    )


class TimestampMixin(BaseModel):
    """Mixin for timestamps in schemas."""

    created_at: datetime
    updated_at: datetime


class UUIDMixin(BaseModel):
    """Mixin for UUID primary key."""

    id: UUID


# ----- Pagination -----

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
        """Return page size as limit."""
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        """Create paginated response.

        Args:
            items: List of items
            total: Total item count
            page: Current page number
            page_size: Items per page

        Returns:
            PaginatedResponse: Paginated response instance
        """
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


# ----- Common Enums -----

from models.enums import (
    DecisionType,
    DeliveryNoteStatus,
    DocumentStatus,
    ExceptionReason,
    ExceptionStatus,
    InvoiceStatus,
    MatchingStatus,
    PurchaseOrderStatus,
)


# ----- Invoice Schemas -----

class InvoiceLineBase(BaseSchema):
    """Base invoice line schema."""

    line_number: int
    description: str = Field(max_length=500)
    sku: str | None = Field(default=None, max_length=100)
    quantity: Decimal = Field(ge=0)
    unit_of_measure: str | None = Field(default=None, max_length=20)
    unit_price: Decimal = Field(ge=0)
    tax_code: str | None = Field(default=None, max_length=20)
    tax_rate: Decimal = Field(default=Decimal("0.00"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    line_total: Decimal = Field(ge=0)


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating invoice line."""

    pass


class InvoiceLineResponse(InvoiceLineBase, UUIDMixin, TimestampMixin):
    """Schema for invoice line response."""

    invoice_id: UUID
    matched_pol_id: UUID | None = None
    matched_dn_line_id: UUID | None = None
    match_score: float | None = None
    is_matched: bool = False


class InvoiceLineUpdate(BaseSchema):
    """Schema for updating invoice line."""

    description: str | None = Field(default=None, max_length=500)
    sku: str | None = Field(default=None, max_length=100)
    quantity: Decimal | None = Field(default=None, ge=0)
    unit_of_measure: str | None = Field(default=None, max_length=20)
    unit_price: Decimal | None = Field(default=None, ge=0)
    tax_code: str | None = Field(default=None, max_length=20)
    tax_rate: Decimal | None = Field(default=None, ge=0)


class InvoiceBase(BaseSchema):
    """Base invoice schema."""

    invoice_number: str = Field(max_length=100)
    vendor_id: str = Field(max_length=100)
    vendor_name: str = Field(max_length=255)
    invoice_date: date
    due_date: date | None = None
    currency: str = Field(default="USD", max_length=3)
    subtotal: Decimal = Field(default=Decimal("0.00"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    total_amount: Decimal = Field(ge=0)
    notes: str | None = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating invoice."""

    lines: list[InvoiceLineCreate] = Field(default_factory=list)

    @field_validator("total_amount")
    @classmethod
    def validate_total(cls, v: Decimal, info) -> Decimal:
        """Validate total equals subtotal + tax."""
        return v


class InvoiceUpdate(BaseSchema):
    """Schema for updating invoice."""

    vendor_name: str | None = Field(default=None, max_length=255)
    due_date: date | None = None
    notes: str | None = None
    status: InvoiceStatus | None = None


class InvoiceResponse(InvoiceBase, UUIDMixin, TimestampMixin):
    """Schema for invoice response."""

    status: InvoiceStatus
    decision_type: DecisionType | None = None
    match_score: float | None = None
    matched_po_id: UUID | None = None
    is_deleted: bool = False
    lines: list[InvoiceLineResponse] = Field(default_factory=list)


class InvoiceListResponse(BaseSchema):
    """Schema for invoice list item (without lines)."""

    id: UUID
    invoice_number: str
    vendor_id: str
    vendor_name: str
    invoice_date: date
    total_amount: Decimal
    currency: str
    status: InvoiceStatus
    match_score: float | None = None
    created_at: datetime


# ----- Purchase Order Schemas -----

class POLineBase(BaseSchema):
    """Base PO line schema."""

    line_number: int
    description: str = Field(max_length=500)
    sku: str | None = Field(default=None, max_length=100)
    quantity_ordered: Decimal = Field(ge=0)
    quantity_received: Decimal = Field(default=Decimal("0"), ge=0)
    quantity_invoiced: Decimal = Field(default=Decimal("0"), ge=0)
    unit_of_measure: str | None = Field(default=None, max_length=20)
    unit_price: Decimal = Field(ge=0)
    tax_code: str | None = Field(default=None, max_length=20)
    tax_rate: Decimal = Field(default=Decimal("0.00"), ge=0)
    line_total: Decimal = Field(ge=0)
    delivery_date: date | None = None


class POLineCreate(POLineBase):
    """Schema for creating PO line."""

    pass


class POLineResponse(POLineBase, UUIDMixin, TimestampMixin):
    """Schema for PO line response."""

    purchase_order_id: UUID
    is_fully_invoiced: bool
    is_fully_received: bool


class PurchaseOrderBase(BaseSchema):
    """Base purchase order schema."""

    po_number: str = Field(max_length=100)
    vendor_id: str = Field(max_length=100)
    vendor_name: str = Field(max_length=255)
    po_date: date
    delivery_date: date | None = None
    currency: str = Field(default="USD", max_length=3)
    subtotal: Decimal = Field(default=Decimal("0.00"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    total_amount: Decimal = Field(ge=0)
    department: str | None = Field(default=None, max_length=100)
    requested_by: str | None = Field(default=None, max_length=255)
    approved_by: str | None = Field(default=None, max_length=255)
    notes: str | None = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating purchase order."""

    lines: list[POLineCreate] = Field(default_factory=list)


class PurchaseOrderResponse(PurchaseOrderBase, UUIDMixin, TimestampMixin):
    """Schema for purchase order response."""

    status: PurchaseOrderStatus
    is_deleted: bool = False
    lines: list[POLineResponse] = Field(default_factory=list)


class PurchaseOrderListResponse(BaseSchema):
    """Schema for PO list item (without lines)."""

    id: UUID
    po_number: str
    vendor_id: str
    vendor_name: str
    po_date: date
    total_amount: Decimal
    currency: str
    status: PurchaseOrderStatus
    created_at: datetime


# ----- Delivery Note Schemas -----

class DNLineBase(BaseSchema):
    """Base delivery note line schema."""

    line_number: int
    description: str = Field(max_length=500)
    sku: str | None = Field(default=None, max_length=100)
    quantity_delivered: Decimal = Field(ge=0)
    quantity_received: Decimal = Field(default=Decimal("0"), ge=0)
    unit_of_measure: str | None = Field(default=None, max_length=20)
    unit_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    line_total: Decimal = Field(ge=0)


class DNLineCreate(DNLineBase):
    """Schema for creating delivery note line."""

    pass


class DNLineResponse(DNLineBase, UUIDMixin, TimestampMixin):
    """Schema for delivery note line response."""

    delivery_note_id: UUID
    matched_pol_id: UUID | None = None
    matched_inv_line_id: UUID | None = None


class DeliveryNoteBase(BaseSchema):
    """Base delivery note schema."""

    dn_number: str = Field(max_length=100)
    vendor_id: str = Field(max_length=100)
    vendor_name: str = Field(max_length=255)
    po_reference: str | None = Field(default=None, max_length=100)
    dn_date: date
    received_date: date | None = None
    currency: str = Field(default="USD", max_length=3)
    total_amount: Decimal = Field(ge=0)
    received_by: str | None = Field(default=None, max_length=255)
    notes: str | None = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating delivery note."""

    lines: list[DNLineCreate] = Field(default_factory=list)


class DeliveryNoteResponse(DeliveryNoteBase, UUIDMixin, TimestampMixin):
    """Schema for delivery note response."""

    status: DeliveryNoteStatus
    po_id: UUID | None = None
    is_deleted: bool = False
    lines: list[DNLineResponse] = Field(default_factory=list)


# ----- Matching Schemas -----

class MatchResultLine(BaseSchema):
    """Match result for a single line."""

    invoice_line_id: UUID
    invoice_line_number: int
    matched_pol_id: UUID | None = None
    matched_pol_line_number: int | None = None
    match_score: float
    match_reason: str
    price_match: bool
    qty_match: bool
    price_variance: Decimal | None = None
    qty_variance: Decimal | None = None


class MatchResult(BaseSchema):
    """Result of matching operation."""

    invoice_id: UUID
    invoice_number: str
    overall_score: float
    decision_type: DecisionType
    lines: list[MatchResultLine]
    matched_po_id: UUID | None = None
    matched_po_number: str | None = None
    total_invoiced: Decimal
    total_matched: Decimal
    unmatched_amount: Decimal


class MatchingTriggerRequest(BaseSchema):
    """Request to trigger matching for an invoice."""

    invoice_id: UUID
    force_rematch: bool = Field(
        default=False,
        description="Force rematch even if already matched",
    )


class MatchingTriggerResponse(BaseSchema):
    """Response for matching trigger."""

    job_id: UUID
    status: MatchingStatus
    message: str


# ----- Exception Schemas -----

class ExceptionBase(BaseSchema):
    """Base exception schema."""

    invoice_id: UUID
    invoice_number: str
    po_id: UUID | None = None
    po_number: str | None = None
    reason: ExceptionReason
    details: str | None = None
    amount_variance: Decimal | None = None
    quantity_variance: Decimal | None = None


class ExceptionResponse(ExceptionBase, UUIDMixin, TimestampMixin):
    """Schema for exception response."""

    status: ExceptionStatus
    resolved_by: str | None = None
    resolved_at: datetime | None = None
    resolution_notes: str | None = None


class ExceptionResolveRequest(BaseSchema):
    """Request to resolve an exception."""

    resolution_notes: str | None = None
    action: str = Field(description="Action taken: approve, reject, adjust")


class ExceptionDismissRequest(BaseSchema):
    """Request to dismiss an exception."""

    reason: str = Field(min_length=10, max_length=500)
    dismiss_as_accepted: bool = Field(
        default=False,
        description="Dismiss and accept the variance",
    )


# ----- Balance Ledger Schemas -----

class BalanceLedgerResponse(BaseSchema):
    """Schema for balance ledger entry."""

    id: UUID
    po_line_id: UUID
    transaction_type: str
    reference_type: str
    reference_id: UUID
    reference_number: str
    quantity_delta: Decimal
    amount_delta: Decimal
    running_quantity: Decimal
    running_amount: Decimal
    currency: str
    transaction_date: datetime
    notes: str | None = None
    created_at: datetime


class POLineBalance(BaseSchema):
    """Balance information for a PO line."""

    po_line_id: UUID
    po_line_number: int
    description: str
    quantity_ordered: Decimal
    quantity_invoiced: Decimal
    quantity_remaining: Decimal
    line_total: Decimal
    amount_invoiced: Decimal
    balance_amount: Decimal
    currency: str
    entries: list[BalanceLedgerResponse] = Field(default_factory=list)


# ----- Cross Reference Schemas -----

class CrossRefResponse(BaseSchema):
    """Schema for cross-reference entry."""

    id: UUID
    source_type: str
    source_sku: str | None = None
    source_description: str | None = None
    target_type: str
    target_sku: str | None = None
    target_description: str | None = None
    vendor_id: str | None = None
    match_count: int
    first_match_date: date
    last_match_date: date
    confidence_score: float
    is_promoted: bool
    is_active: bool


# ----- Health Check -----

class HealthResponse(BaseSchema):
    """Health check response."""

    status: str
    version: str
    database: str
    timestamp: datetime

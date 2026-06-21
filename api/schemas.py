# api/schemas.py
"""Shared Pydantic schemas for API request/response models.

Contains common schemas used across all API endpoints including
pagination, filtering, and standard response formats.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict


T = TypeVar("T")


class BaseFilterParams(BaseModel):
    """Base filtering and pagination parameters."""

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    sort_by: str | None = Field(default=None, description="Sort field")
    sort_order: str = Field(default="asc", pattern="^(asc|desc)$", description="Sort order")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""

    items: list[T]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total_pages: int = Field(ge=0)

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        """Create a paginated response."""
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(description="Error code")
    message: str = Field(description="Human-readable error message")
    details: list[dict] | None = Field(default=None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuccessResponse(BaseModel):
    """Standard success response."""

    message: str = Field(description="Success message")
    data: dict | None = Field(default=None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Invoice schemas
class InvoiceLineBase(BaseModel):
    """Base invoice line schema."""

    line_number: int = Field(ge=1)
    description: str = Field(max_length=500)
    sku: str | None = Field(default=None, max_length=100)
    quantity: Decimal = Field(ge=0)
    unit_price: Decimal = Field(ge=0)
    line_amount: Decimal = Field(ge=0)
    tax_rate: Decimal | None = Field(default=None, ge=0)
    tax_amount: Decimal | None = Field(default=None, ge=0)


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating an invoice line."""

    matched_po_line_id: UUID | None = None
    matched_dn_line_id: UUID | None = None
    match_score: float | None = None


class InvoiceLineResponse(InvoiceLineBase):
    """Invoice line response schema."""

    id: UUID
    invoice_id: UUID
    matched_po_line_id: UUID | None = None
    matched_dn_line_id: UUID | None = None
    match_score: float | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoiceBase(BaseModel):
    """Base invoice schema."""

    invoice_number: str = Field(max_length=100)
    supplier_id: str = Field(max_length=100)
    supplier_name: str = Field(max_length=255)
    invoice_date: date
    due_date: date | None = None
    total_amount: Decimal = Field(ge=0)
    tax_amount: Decimal | None = Field(default=None, ge=0)
    currency: str = Field(default="USD", max_length=3)
    notes: str | None = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating an invoice."""

    lines: list[InvoiceLineCreate] = Field(default_factory=list)
    created_by: str | None = None


class InvoiceUpdate(BaseModel):
    """Schema for updating an invoice."""

    supplier_name: str | None = None
    due_date: date | None = None
    notes: str | None = None
    status: str | None = None


class InvoiceResponse(InvoiceBase):
    """Invoice response schema."""

    id: UUID
    status: str
    matching_status: str
    matched_po_id: UUID | None = None
    matched_dn_id: UUID | None = None
    match_score: float | None = None
    decision_type: str | None = None
    lines: list[InvoiceLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Purchase Order schemas
class POLineBase(BaseModel):
    """Base PO line schema."""

    line_number: int = Field(ge=1)
    description: str = Field(max_length=500)
    sku: str | None = Field(default=None, max_length=100)
    quantity: Decimal = Field(ge=0)
    delivered_quantity: Decimal = Field(default=Decimal("0"), ge=0)
    unit_price: Decimal = Field(ge=0)
    line_amount: Decimal = Field(ge=0)
    expected_delivery_date: date | None = None


class POLineCreate(POLineBase):
    """Schema for creating a PO line."""

    pass


class POLineResponse(POLineBase):
    """PO line response schema."""

    id: UUID
    po_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderBase(BaseModel):
    """Base purchase order schema."""

    po_number: str = Field(max_length=100)
    supplier_id: str = Field(max_length=100)
    supplier_name: str = Field(max_length=255)
    order_date: date
    expected_delivery_date: date | None = None
    delivery_date: date | None = None
    total_amount: Decimal = Field(ge=0)
    currency: str = Field(default="USD", max_length=3)
    notes: str | None = None
    erp_reference: str | None = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a purchase order."""

    lines: list[POLineCreate] = Field(default_factory=list)
    created_by: str | None = None


class PurchaseOrderResponse(PurchaseOrderBase):
    """Purchase order response schema."""

    id: UUID
    status: str
    lines: list[POLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Delivery Note schemas
class DNLineBase(BaseModel):
    """Base delivery note line schema."""

    line_number: int = Field(ge=1)
    description: str = Field(max_length=500)
    sku: str | None = Field(default=None, max_length=100)
    quantity: Decimal = Field(ge=0)
    unit_price: Decimal | None = Field(default=None, ge=0)
    line_amount: Decimal | None = Field(default=None, ge=0)


class DNLineCreate(DNLineBase):
    """Schema for creating a DN line."""

    matched_po_line_id: UUID | None = None


class DNLineResponse(DNLineBase):
    """DN line response schema."""

    id: UUID
    dn_id: UUID
    matched_po_line_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeliveryNoteBase(BaseModel):
    """Base delivery note schema."""

    dn_number: str = Field(max_length=100)
    supplier_id: str = Field(max_length=100)
    supplier_name: str = Field(max_length=255)
    po_reference: str | None = None
    delivery_date: date
    total_amount: Decimal = Field(ge=0)
    currency: str = Field(default="USD", max_length=3)
    notes: str | None = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating a delivery note."""

    lines: list[DNLineCreate] = Field(default_factory=list)
    created_by: str | None = None


class DeliveryNoteResponse(DeliveryNoteBase):
    """Delivery note response schema."""

    id: UUID
    status: str
    related_po_id: UUID | None = None
    lines: list[DNLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Matching schemas
class MatchingRequest(BaseModel):
    """Request to trigger matching for an invoice."""

    invoice_id: UUID
    force_rematch: bool = Field(default=False, description="Force rematch even if already matched")


class MatchResultLine(BaseModel):
    """Match result for a single line."""

    invoice_line_id: UUID
    po_line_id: UUID | None = None
    dn_line_id: UUID | None = None
    match_score: float
    match_type: str | None = None
    price_variance: Decimal | None = None
    qty_variance: Decimal | None = None
    cross_ref_id: UUID | None = None


class MatchingResponse(BaseModel):
    """Matching result response."""

    invoice_id: UUID
    overall_score: float
    decision_type: str
    lines: list[MatchResultLine]
    exceptions: list[dict] = Field(default_factory=list)
    matched_po_id: UUID | None = None
    matched_dn_id: UUID | None = None
    processing_time_ms: int


# Exception schemas
class ExceptionResponse(BaseModel):
    """Exception response schema."""

    id: UUID
    invoice_id: UUID
    exception_type: str
    message: str
    severity: str
    status: str
    resolved_by: str | None = None
    resolved_at: datetime | None = None
    resolution_notes: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExceptionResolveRequest(BaseModel):
    """Request to resolve an exception."""

    resolution_notes: str = Field(max_length=1000)
    action: str = Field(pattern="^(resolve|dismiss|escalate)$")


class BalanceResponse(BaseModel):
    """Balance ledger response."""

    id: UUID
    po_line_id: UUID
    transaction_type: str
    transaction_id: UUID
    amount: Decimal
    balance_after: Decimal
    currency: str
    description: str | None = None
    reference_number: str | None = None
    transaction_date: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BalanceSummary(BaseModel):
    """Balance summary for a PO line."""

    po_line_id: UUID
    original_quantity: Decimal
    delivered_quantity: Decimal
    invoiced_quantity: Decimal
    paid_quantity: Decimal
    outstanding_quantity: Decimal
    original_amount: Decimal
    invoiced_amount: Decimal
    paid_amount: Decimal
    outstanding_amount: Decimal
    currency: str

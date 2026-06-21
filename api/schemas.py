// api/schemas.py
"""Shared Pydantic schemas for API request/response models."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from models.enums import (
    DecisionType,
    DocumentStatus,
    ExceptionReason,
    ExceptionStatus,
    LearningStatus,
    MatchStatus,
    MatchType,
)


# Generic type for pagination
T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters."""

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate offset for query."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Get limit for query."""
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
        """Create a paginated response."""
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


# Base schemas
class TimestampSchema(BaseModel):
    """Schema with timestamp fields."""

    created_at: datetime
    updated_at: datetime


# Invoice schemas
class InvoiceLineBase(BaseModel):
    """Base schema for invoice line."""

    line_number: str
    description: str
    sku: str | None = None
    product_code: str | None = None
    unit_of_measure: str = "EA"
    quantity: Annotated[Decimal, Field(ge=0, decimal_places=3)]
    unit_price: Annotated[Decimal, Field(ge=0, decimal_places=4)]
    line_amount: Annotated[Decimal, Field(ge=0, decimal_places=2)]
    tax_amount: Decimal | None = None

    model_config = ConfigDict(from_attributes=True)


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating invoice line."""

    po_line_id: UUID | None = None


class InvoiceLineResponse(InvoiceLineBase):
    """Schema for invoice line response."""

    id: UUID
    invoice_id: UUID
    po_line_id: UUID | None = None
    matched_quantity: Decimal = Decimal("0")
    match_status: str | None = None

    model_config = ConfigDict(from_attributes=True)


class InvoiceBase(BaseModel):
    """Base schema for invoice."""

    vendor_number: str
    vendor_name: str
    vendor_address: str | None = None
    invoice_number: str
    invoice_date: date
    due_date: date | None = None
    received_date: date
    total_amount: Annotated[Decimal, Field(ge=0, decimal_places=2)]
    tax_amount: Decimal | None = None
    currency: str = "USD"
    notes: str | None = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating invoice."""

    lines: list[InvoiceLineCreate] = Field(default_factory=list)
    source_system: str = "manual"


class InvoiceUpdate(BaseModel):
    """Schema for updating invoice."""

    status: DocumentStatus | None = None
    notes: str | None = None
    due_date: date | None = None


class InvoiceResponse(InvoiceBase):
    """Schema for invoice response."""

    id: UUID
    status: str
    is_paid: bool
    erp_invoice_id: str | None = None
    source_system: str
    created_at: datetime
    updated_at: datetime
    lines: list[InvoiceLineResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# Purchase Order schemas
class PurchaseOrderLineBase(BaseModel):
    """Base schema for PO line."""

    line_number: str
    description: str
    sku: str | None = None
    product_code: str | None = None
    unit_of_measure: str = "EA"
    quantity_ordered: Annotated[Decimal, Field(ge=0, decimal_places=3)]
    quantity_received: Decimal = Decimal("0")
    unit_price: Annotated[Decimal, Field(ge=0, decimal_places=4)]
    line_amount: Annotated[Decimal, Field(ge=0, decimal_places=2)]
    expected_delivery_date: date | None = None

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Schema for creating PO line."""

    pass


class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    """Schema for PO line response."""

    id: UUID
    po_id: UUID
    quantity_open: Decimal

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderBase(BaseModel):
    """Base schema for purchase order."""

    vendor_number: str
    vendor_name: str
    vendor_address: str | None = None
    po_number: str
    po_date: date
    expected_delivery_date: date | None = None
    total_amount: Annotated[Decimal, Field(ge=0, decimal_places=2)]
    currency: str = "USD"


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating purchase order."""

    lines: list[PurchaseOrderLineCreate] = Field(default_factory=list)
    source_system: str = "erp"


class PurchaseOrderResponse(PurchaseOrderBase):
    """Schema for purchase order response."""

    id: UUID
    status: str
    erp_po_id: str | None = None
    source_system: str
    is_approved: bool
    approved_by: str | None = None
    approved_at: date | None = None
    created_at: datetime
    updated_at: datetime
    lines: list[PurchaseOrderLineResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# Delivery Note schemas
class DeliveryNoteLineBase(BaseModel):
    """Base schema for DN line."""

    line_number: str
    description: str
    sku: str | None = None
    product_code: str | None = None
    unit_of_measure: str = "EA"
    quantity_delivered: Annotated[Decimal, Field(ge=0, decimal_places=3)]
    quantity_accepted: Decimal = Decimal("0")
    quantity_rejected: Decimal = Decimal("0")
    po_line_id: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating DN line."""

    pass


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """Schema for DN line response."""

    id: UUID
    dn_id: UUID

    model_config = ConfigDict(from_attributes=True)


class DeliveryNoteBase(BaseModel):
    """Base schema for delivery note."""

    vendor_number: str
    vendor_name: str
    dn_number: str
    delivery_date: date
    received_by: str | None = None
    po_number: str | None = None
    po_id: UUID | None = None
    source_system: str = "warehouse"


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating delivery note."""

    lines: list[DeliveryNoteLineCreate] = Field(default_factory=list)


class DeliveryNoteResponse(DeliveryNoteBase):
    """Schema for delivery note response."""

    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    lines: list[DeliveryNoteLineResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# Matching schemas
class MatchResultLine(BaseModel):
    """Match result for a single line."""

    invoice_line_id: UUID
    invoice_line_number: str
    invoice_description: str
    invoice_quantity: Decimal
    invoice_unit_price: Decimal
    matched_po_line_id: UUID | None = None
    matched_po_line_number: str | None = None
    matched_quantity: Decimal = Decimal("0")
    match_type: MatchType | None = None
    match_score: Decimal = Decimal("0")
    price_variance: Decimal = Decimal("0")
    quantity_variance: Decimal = Decimal("0")


class MatchResult(BaseModel):
    """Match result for an invoice."""

    invoice_id: UUID
    invoice_number: str
    decision: DecisionType
    overall_score: Decimal
    matched_lines: list[MatchResultLine] = Field(default_factory=list)
    unmatched_lines: list[MatchResultLine] = Field(default_factory=list)
    exceptions: list["ExceptionDetail"] = Field(default_factory=list)


class MatchResultResponse(MatchResult):
    """Response schema for match result."""

    id: UUID
    created_at: datetime


# Exception schemas
class ExceptionDetail(BaseModel):
    """Exception detail for matching issues."""

    reason: ExceptionReason
    message: str
    invoice_line_id: UUID | None = None
    po_line_id: UUID | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class ExceptionCreate(BaseModel):
    """Schema for creating exception."""

    invoice_id: UUID
    reason: ExceptionReason
    message: str
    invoice_line_id: UUID | None = None
    po_line_id: UUID | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class ExceptionResponse(BaseModel):
    """Schema for exception response."""

    id: UUID
    invoice_id: UUID
    reason: str
    message: str
    status: str
    invoice_line_id: UUID | None = None
    po_line_id: UUID | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    resolved_at: datetime | None = None
    resolved_by: str | None = None
    resolution_notes: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ExceptionResolve(BaseModel):
    """Schema for resolving exception."""

    resolution: str = Field(min_length=1, max_length=500)
    notes: str | None = None


# Balance Ledger schemas
class BalanceLedgerResponse(BaseModel):
    """Schema for balance ledger response."""

    id: UUID
    po_line_id: UUID
    invoice_line_id: UUID | None = None
    transaction_type: str
    po_quantity: Decimal
    previous_balance_quantity: Decimal
    transaction_quantity: Decimal
    current_balance_quantity: Decimal
    po_amount: Decimal
    previous_balance_amount: Decimal
    transaction_amount: Decimal
    current_balance_amount: Decimal
    reference_number: str | None = None
    notes: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# CrossRef/ Learning schemas
class CrossRefResponse(BaseModel):
    """Schema for cross-reference response."""

    id: UUID
    vendor_number: str
    invoice_sku: str | None = None
    invoice_product_code: str | None = None
    po_sku: str | None = None
    po_product_code: str | None = None
    match_score: Decimal
    confidence_score: Decimal
    confirmation_count: int
    rejection_count: int
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CrossRefConfirm(BaseModel):
    """Schema for confirming cross-ref."""

    cross_ref_id: UUID
    confirmed: bool
    notes: str | None = None


# Health check
class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    database: str
    version: str


# Error response
class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    detail: str | None = None
    code: str | None = None


# Update forward references
MatchResult.model_rebuild()

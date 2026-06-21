// api/schemas.py
"""Shared Pydantic request/response models.

This module defines common Pydantic models used across API endpoints:
- Pagination parameters
- Standard response wrappers
- Common field definitions
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Generic type for response data
T = TypeVar("T")


# ============================================================
# Pagination Models
# ============================================================

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
        """Get limit for database query."""
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""

    items: list[T]
    total: int = Field(ge=0, description="Total number of items")
    page: int = Field(ge=1, description="Current page")
    page_size: int = Field(ge=1, description="Items per page")
    total_pages: int = Field(ge=0, description="Total number of pages")

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        """Create a paginated response.

        Args:
            items: List of items for current page
            total: Total number of items
            page: Current page number
            page_size: Items per page

        Returns:
            PaginatedResponse: The paginated response
        """
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


# ============================================================
# Standard Response Models
# ============================================================

class BaseResponse(BaseModel):
    """Base response model."""

    success: bool = True
    message: str | None = None


class ErrorResponse(BaseModel):
    """Error response model."""

    success: bool = False
    error: str
    detail: str | None = None
    code: str | None = None


class DataResponse(BaseModel, Generic[T]):
    """Generic data response wrapper."""

    success: bool = True
    data: T
    message: str | None = None


# ============================================================
# Invoice Schemas
# ============================================================

class InvoiceLineItem(BaseModel):
    """Invoice line item for ingestion."""

    line_number: int
    item_code: str | None = None
    item_description: str
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    line_amount: Decimal = Field(ge=0)
    uom: str = "EA"


class InvoiceCreate(BaseModel):
    """Request model for creating/inhesting an invoice."""

    invoice_number: str = Field(min_length=1, max_length=100)
    vendor_code: str = Field(min_length=1, max_length=50)
    vendor_name: str = Field(min_length=1, max_length=255)
    invoice_date: date
    due_date: date | None = None
    total_amount: Decimal = Field(gt=0)
    tax_amount: Decimal = Field(ge=0, default=Decimal("0.00"))
    currency: str = Field(default="USD", min_length=3, max_length=3)
    po_reference: str | None = None
    notes: str | None = None
    line_items: list[InvoiceLineItem] | None = None

    model_config = ConfigDict(json_encoders={Decimal: lambda v: float(v)})


class InvoiceUpdate(BaseModel):
    """Request model for updating an invoice."""

    status: str | None = None
    due_date: date | None = None
    notes: str | None = None
    approved_by: str | None = None


class InvoiceResponse(BaseModel):
    """Response model for invoice."""

    id: UUID
    invoice_number: str
    vendor_code: str
    vendor_name: str
    invoice_date: date
    due_date: date | None
    total_amount: Decimal
    tax_amount: Decimal
    currency: str
    status: str
    po_reference: str | None
    notes: str | None
    is_ocr_processed: bool
    ocr_confidence: float
    match_score: float | None
    match_decision: str | None
    approved_at: datetime | None
    approved_by: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoiceListResponse(BaseModel):
    """Response model for invoice list item (lighter weight)."""

    id: UUID
    invoice_number: str
    vendor_code: str
    vendor_name: str
    invoice_date: date
    total_amount: Decimal
    currency: str
    status: str
    match_score: float | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Purchase Order Schemas
# ============================================================

class POLineItem(BaseModel):
    """PO line item for ingestion."""

    line_number: int
    item_code: str = Field(min_length=1, max_length=50)
    item_description: str = Field(min_length=1, max_length=500)
    quantity: Decimal = Field(gt=0)
    quantity_received: Decimal = Field(ge=0, default=Decimal("0"))
    unit_price: Decimal = Field(ge=0)
    line_amount: Decimal = Field(ge=0)
    expected_delivery_date: date | None = None
    uom: str = "EA"


class PurchaseOrderCreate(BaseModel):
    """Request model for creating/ingesting a PO."""

    po_number: str = Field(min_length=1, max_length=100)
    vendor_code: str = Field(min_length=1, max_length=50)
    vendor_name: str = Field(min_length=1, max_length=255)
    po_date: date
    expected_delivery_date: date | None = None
    total_amount: Decimal = Field(gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    erp_reference: str | None = None
    notes: str | None = None
    line_items: list[POLineItem] | None = None

    model_config = ConfigDict(json_encoders={Decimal: lambda v: float(v)})


class PurchaseOrderResponse(BaseModel):
    """Response model for purchase order."""

    id: UUID
    po_number: str
    vendor_code: str
    vendor_name: str
    po_date: date
    expected_delivery_date: date | None
    total_amount: Decimal
    currency: str
    status: str
    is_active: bool
    erp_reference: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderListResponse(BaseModel):
    """Response model for PO list item."""

    id: UUID
    po_number: str
    vendor_code: str
    vendor_name: str
    po_date: date
    total_amount: Decimal
    currency: str
    status: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Delivery Note Schemas
# ============================================================

class DNLineItem(BaseModel):
    """Delivery note line item."""

    line_number: int
    item_code: str = Field(min_length=1, max_length=50)
    item_description: str | None = None
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal | None = None
    uom: str = "EA"
    po_line_reference: UUID | None = None


class DeliveryNoteCreate(BaseModel):
    """Request model for creating a delivery note."""

    dn_number: str = Field(min_length=1, max_length=100)
    vendor_code: str = Field(min_length=1, max_length=50)
    vendor_name: str = Field(min_length=1, max_length=255)
    po_reference: str | None = None
    receipt_date: date
    expected_delivery_date: date | None = None
    total_amount: Decimal = Field(ge=0, default=Decimal("0.00"))
    currency: str = Field(default="USD", min_length=3, max_length=3)
    warehouse_location: str | None = None
    received_by: str | None = None
    notes: str | None = None
    line_items: list[DNLineItem] | None = None

    model_config = ConfigDict(json_encoders={Decimal: lambda v: float(v)})


class DeliveryNoteResponse(BaseModel):
    """Response model for delivery note."""

    id: UUID
    dn_number: str
    vendor_code: str
    vendor_name: str
    po_reference: str | None
    receipt_date: date
    expected_delivery_date: date | None
    total_amount: Decimal
    currency: str
    status: str
    warehouse_location: str | None
    received_by: str | None
    notes: str | None
    is_ocr_processed: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Matching Schemas
# ============================================================

class MatchTriggerRequest(BaseModel):
    """Request model for triggering matching."""

    invoice_id: UUID
    auto_process: bool = Field(default=True, description="Auto-process after matching")


class MatchResultLine(BaseModel):
    """Match result for a single line."""

    po_line_id: UUID | None
    item_code: str
    invoice_qty: Decimal
    invoice_amount: Decimal
    matched_qty: Decimal
    matched_amount: Decimal
    price_variance: float
    qty_variance: float
    line_score: float


class MatchResultResponse(BaseModel):
    """Response model for match result."""

    invoice_id: UUID
    purchase_order_id: UUID | None
    overall_score: float
    decision: str
    decision_reason: str
    lines: list[MatchResultLine]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MatchDecisionUpdate(BaseModel):
    """Request model for updating match decision."""

    invoice_id: UUID
    decision: str = Field(
        description="New decision: auto_approved, review_required, exception, rejected"
    )
    notes: str | None = None
    approved_by: str | None = None


# ============================================================
# Exception Schemas
# ============================================================

class ExceptionCreate(BaseModel):
    """Request model for creating an exception."""

    invoice_id: UUID
    exception_type: str
    description: str
    po_line_id: UUID | None = None
    variance_amount: Decimal | None = None
    variance_percentage: float | None = None


class ExceptionResponse(BaseModel):
    """Response model for exception."""

    id: UUID
    invoice_id: UUID
    exception_type: str
    description: str
    po_line_id: UUID | None
    variance_amount: Decimal | None
    variance_percentage: float | None
    status: str
    resolution: str | None
    resolved_by: str | None
    resolved_at: datetime | None
    resolution_notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExceptionResolveRequest(BaseModel):
    """Request model for resolving an exception."""

    resolution: str = Field(
        description="Resolution: approved_as_is, adjusted, dismissed, escalated, write_off, manual_override"
    )
    resolution_notes: str | None = None
    adjusted_amount: Decimal | None = None
    resolved_by: str


# ============================================================
# Balance Ledger Schemas
# ============================================================

class BalanceLedgerResponse(BaseModel):
    """Response model for balance ledger entry."""

    id: UUID
    purchase_order_id: UUID | None
    po_line_id: UUID | None
    invoice_id: UUID | None
    item_code: str
    ordered_qty: Decimal
    received_qty: Decimal
    invoiced_qty: Decimal
    paid_qty: Decimal
    line_amount: Decimal
    invoiced_amount: Decimal
    paid_amount: Decimal
    open_qty: Decimal
    open_amount: Decimal
    currency: str
    last_activity_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Statistics / Dashboard Schemas
# ============================================================

class DashboardStats(BaseModel):
    """Dashboard statistics response."""

    total_invoices: int
    pending_invoices: int
    matched_invoices: int
    approved_invoices: int
    rejected_invoices: int
    total_exceptions: int
    open_exceptions: int
    resolved_exceptions: int
    average_match_score: float | None
    auto_approve_rate: float

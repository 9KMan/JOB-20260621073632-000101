// api/schemas.py
"""Shared Pydantic request/response models."""
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        pagination: PaginationParams,
    ) -> "PaginatedResponse[T]":
        """Create a paginated response."""
        total_pages = (total + pagination.page_size - 1) // pagination.page_size
        return cls(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages,
        )


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    service: str
    version: Optional[str] = None


# === Invoice Schemas ===


class InvoiceLineCreate(BaseModel):
    """Schema for creating an invoice line."""

    line_number: str
    description: Optional[str] = None
    quantity: Decimal
    unit_of_measure: Optional[str] = None
    unit_price: Decimal
    line_amount: Decimal
    po_line_id: Optional[str] = None
    dn_line_id: Optional[str] = None

    model_config = ConfigDict(decimal_places=4)


class InvoiceLineResponse(BaseModel):
    """Schema for invoice line response."""

    id: str
    line_number: str
    description: Optional[str]
    quantity: Decimal
    unit_of_measure: Optional[str]
    unit_price: Decimal
    line_amount: Decimal
    po_line_id: Optional[str]
    dn_line_id: Optional[str]
    match_status: Optional[str]
    match_score: Optional[Decimal]

    model_config = ConfigDict(from_attributes=True)


class InvoiceCreate(BaseModel):
    """Schema for creating an invoice."""

    vendor_number: str
    vendor_name: str
    vendor_tax_id: Optional[str] = None
    invoice_number: str
    invoice_date: date
    due_date: Optional[date] = None
    invoice_amount: Decimal
    tax_amount: Optional[Decimal] = None
    currency_code: str = "USD"
    description: Optional[str] = None
    payment_terms: Optional[str] = None
    lines: List[InvoiceLineCreate]

    @field_validator("invoice_amount", "tax_amount", "lines")
    @classmethod
    def validate_amounts(cls, v, info):
        if info.field_name == "invoice_amount" and v < 0:
            raise ValueError("Invoice amount cannot be negative")
        return v


class InvoiceResponse(BaseModel):
    """Schema for invoice response."""

    id: str
    vendor_number: str
    vendor_name: str
    vendor_tax_id: Optional[str]
    invoice_number: str
    invoice_date: date
    due_date: Optional[date]
    invoice_amount: Decimal
    tax_amount: Optional[Decimal]
    currency_code: str
    po_id: Optional[str]
    dn_id: Optional[str]
    status: str
    match_decision: Optional[str]
    match_score: Optional[Decimal]
    match_confidence: Optional[str]
    description: Optional[str]
    payment_terms: Optional[str]
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    lines: List[InvoiceLineResponse]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoiceUpdate(BaseModel):
    """Schema for updating an invoice."""

    status: Optional[str] = None
    approved_by: Optional[str] = None
    description: Optional[str] = None


# === Purchase Order Schemas ===


class PurchaseOrderLineCreate(BaseModel):
    """Schema for creating a PO line."""

    line_number: str
    description: Optional[str] = None
    quantity: Decimal
    unit_of_measure: Optional[str] = None
    unit_price: Decimal
    line_amount: Decimal
    tax_code: Optional[str] = None


class PurchaseOrderCreate(BaseModel):
    """Schema for creating a purchase order."""

    vendor_number: str
    vendor_name: str
    vendor_tax_id: Optional[str] = None
    po_number: str
    po_date: date
    delivery_date: Optional[date] = None
    po_amount: Decimal
    currency_code: str = "USD"
    description: Optional[str] = None
    payment_terms: Optional[str] = None
    shipping_terms: Optional[str] = None
    requested_by: Optional[str] = None
    lines: List[PurchaseOrderLineCreate]


class PurchaseOrderLineResponse(BaseModel):
    """Schema for PO line response."""

    id: str
    line_number: str
    description: Optional[str]
    quantity: Decimal
    received_quantity: Decimal
    unit_of_measure: Optional[str]
    unit_price: Decimal
    line_amount: Decimal
    tax_code: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderResponse(BaseModel):
    """Schema for purchase order response."""

    id: str
    vendor_number: str
    vendor_name: str
    vendor_tax_id: Optional[str]
    po_number: str
    po_date: date
    delivery_date: Optional[date]
    po_amount: Decimal
    currency_code: str
    status: str
    description: Optional[str]
    payment_terms: Optional[str]
    shipping_terms: Optional[str]
    requested_by: Optional[str]
    lines: List[PurchaseOrderLineResponse]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# === Delivery Note Schemas ===


class DeliveryNoteLineCreate(BaseModel):
    """Schema for creating a DN line."""

    line_number: str
    description: Optional[str] = None
    quantity: Decimal
    unit_of_measure: Optional[str] = None
    unit_price: Optional[Decimal] = None
    line_amount: Decimal
    po_line_id: Optional[str] = None


class DeliveryNoteCreate(BaseModel):
    """Schema for creating a delivery note."""

    vendor_number: str
    vendor_name: str
    dn_number: str
    dn_date: date
    delivery_date: Optional[date] = None
    dn_amount: Decimal
    currency_code: str = "USD"
    po_id: Optional[str] = None
    description: Optional[str] = None
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    lines: List[DeliveryNoteLineCreate]


class DeliveryNoteLineResponse(BaseModel):
    """Schema for DN line response."""

    id: str
    line_number: str
    description: Optional[str]
    quantity: Decimal
    unit_of_measure: Optional[str]
    unit_price: Optional[Decimal]
    line_amount: Decimal
    po_line_id: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class DeliveryNoteResponse(BaseModel):
    """Schema for delivery note response."""

    id: str
    vendor_number: str
    vendor_name: str
    dn_number: str
    dn_date: date
    delivery_date: Optional[date]
    dn_amount: Decimal
    currency_code: str
    po_id: Optional[str]
    status: str
    description: Optional[str]
    carrier: Optional[str]
    tracking_number: Optional[str]
    lines: List[DeliveryNoteLineResponse]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# === Matching Schemas ===


class MatchTriggerRequest(BaseModel):
    """Schema for triggering a match."""

    invoice_id: str
    force_rematch: bool = False


class MatchResultResponse(BaseModel):
    """Schema for match result response."""

    invoice_id: str
    match_decision: str
    match_score: Optional[Decimal]
    match_confidence: Optional[str]
    po_id: Optional[str]
    dn_id: Optional[str]
    matched_lines: List[dict]
    threshold_applied: str
    exceptions: List[dict]


class MatchScoreDetail(BaseModel):
    """Detailed score breakdown for a match."""

    total_score: Decimal
    price_score: Optional[Decimal]
    quantity_score: Optional[Decimal]
    date_score: Optional[Decimal]
    vendor_score: Optional[Decimal]
    cross_ref_score: Optional[Decimal]


# === Exception Schemas ===


class ExceptionCreate(BaseModel):
    """Schema for creating an exception."""

    invoice_id: str
    exception_type: str
    description: str
    po_id: Optional[str] = None
    dn_id: Optional[str] = None


class ExceptionResponse(BaseModel):
    """Schema for exception response."""

    id: str
    invoice_id: str
    exception_type: str
    status: str
    description: str
    po_id: Optional[str]
    dn_id: Optional[str]
    resolution_notes: Optional[str]
    resolved_by: Optional[str]
    resolved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExceptionResolveRequest(BaseModel):
    """Schema for resolving an exception."""

    resolution_notes: str
    resolved_by: str


# === Balance Ledger Schemas ===


class BalanceResponse(BaseModel):
    """Schema for balance response."""

    po_id: str
    po_line_id: Optional[str]
    entry_type: str
    quantity_balance: Decimal
    amount_balance: Decimal
    last_updated: datetime


class LedgerEntryResponse(BaseModel):
    """Schema for ledger entry response."""

    id: str
    po_id: str
    po_line_id: Optional[str]
    entry_type: str
    reference_type: str
    reference_id: str
    quantity_delta: Decimal
    quantity_balance_before: Decimal
    quantity_balance_after: Decimal
    amount_delta: Decimal
    amount_balance_before: Decimal
    amount_balance_after: Decimal
    notes: Optional[str]
    processed_at: datetime

    model_config = ConfigDict(from_attributes=True)


# === Cross Reference Schemas ===


class CrossReferenceResponse(BaseModel):
    """Schema for cross-reference response."""

    id: str
    vendor_number: str
    vendor_name: Optional[str]
    vendor_part_number: str
    internal_part_number: Optional[str]
    po_number: Optional[str]
    po_line_number: Optional[str]
    unit_price: Decimal
    unit_of_measure: Optional[str]
    confirmed_count: int
    promotion_level: int
    last_confirmed_at: Optional[datetime]
    last_match_score: Optional[Decimal]
    is_active: bool
    is_approved: bool

    model_config = ConfigDict(from_attributes=True)

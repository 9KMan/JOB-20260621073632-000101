# api/schemas.py
"""Shared Pydantic schemas for request/response validation."""
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator


# Generic type for response wrapper
T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_encoders={Decimal: str, datetime: lambda v: v.isoformat()},
    )


class PaginationMeta(BaseModel):
    """Pagination metadata."""

    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse(BaseSchema, Generic[T]):
    """Generic paginated response wrapper."""

    data: List[T]
    meta: PaginationMeta


class ErrorResponse(BaseSchema):
    """Error response schema."""

    detail: str
    code: Optional[str] = None
    errors: Optional[List[dict]] = None


class SuccessResponse(BaseSchema):
    """Generic success response."""

    success: bool = True
    message: str
    data: Optional[dict] = None


# Invoice Schemas
class InvoiceLineBase(BaseSchema):
    """Base invoice line schema."""

    line_number: int
    description: str
    quantity: Decimal
    unit_price: Decimal
    extended_amount: Decimal
    tax_rate: Optional[Decimal] = Decimal("0.00")
    tax_amount: Optional[Decimal] = Decimal("0.00")
    product_code: Optional[str] = None


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating invoice line."""

    po_line_id: Optional[uuid.UUID] = None
    delivery_note_line_id: Optional[uuid.UUID] = None


class InvoiceLineResponse(InvoiceLineBase):
    """Invoice line response schema."""

    id: uuid.UUID
    po_line_id: Optional[uuid.UUID] = None
    delivery_note_line_id: Optional[uuid.UUID] = None
    is_matched: bool = False
    match_confidence: Optional[float] = None


class InvoiceBase(BaseSchema):
    """Base invoice schema."""

    vendor_id: uuid.UUID
    vendor_name: str
    vendor_code: Optional[str] = None
    invoice_number: str
    invoice_date: str
    due_date: Optional[str] = None
    subtotal: Decimal
    tax_amount: Decimal = Decimal("0.00")
    total_amount: Decimal
    currency: str = "USD"
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating an invoice."""

    lines: List[InvoiceLineCreate]
    source_system: str = "manual"


class InvoiceUpdate(BaseSchema):
    """Schema for updating an invoice."""

    vendor_name: Optional[str] = None
    due_date: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class InvoiceResponse(InvoiceBase):
    """Invoice response schema."""

    id: uuid.UUID
    status: str
    matched_at: Optional[str] = None
    approved_at: Optional[str] = None
    source_system: str
    created_at: datetime
    updated_at: datetime
    lines: List[InvoiceLineResponse] = []


class InvoiceListResponse(BaseSchema):
    """Invoice list item (without lines)."""

    id: uuid.UUID
    vendor_id: uuid.UUID
    vendor_name: str
    invoice_number: str
    invoice_date: str
    total_amount: Decimal
    currency: str
    status: str
    created_at: datetime


# Purchase Order Schemas
class PurchaseOrderLineBase(BaseSchema):
    """Base PO line schema."""

    line_number: int
    description: str
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    quantity_ordered: Decimal
    unit_price: Decimal
    extended_amount: Decimal
    tax_rate: Optional[Decimal] = Decimal("0.00")
    tax_amount: Optional[Decimal] = Decimal("0.00")


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Schema for creating PO line."""

    pass


class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    """PO line response schema."""

    id: uuid.UUID
    quantity_received: Decimal = Decimal("0.000")
    quantity_invoiced: Decimal = Decimal("0.000")
    is_fully_received: bool = False


class PurchaseOrderBase(BaseSchema):
    """Base purchase order schema."""

    vendor_id: uuid.UUID
    vendor_name: str
    vendor_code: Optional[str] = None
    po_number: str
    po_date: str
    expected_delivery_date: Optional[str] = None
    subtotal: Decimal
    tax_amount: Decimal = Decimal("0.00")
    total_amount: Decimal
    currency: str = "USD"
    terms: Optional[str] = None
    notes: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a purchase order."""

    lines: List[PurchaseOrderLineCreate]
    source_system: str = "erp"


class PurchaseOrderResponse(PurchaseOrderBase):
    """Purchase order response schema."""

    id: uuid.UUID
    status: str
    source_system: str
    created_at: datetime
    updated_at: datetime
    lines: List[PurchaseOrderLineResponse] = []


class PurchaseOrderListResponse(BaseSchema):
    """Purchase order list item (without lines)."""

    id: uuid.UUID
    vendor_id: uuid.UUID
    vendor_name: str
    po_number: str
    po_date: str
    total_amount: Decimal
    currency: str
    status: str
    created_at: datetime


# Delivery Note Schemas
class DeliveryNoteLineBase(BaseSchema):
    """Base DN line schema."""

    line_number: int
    description: str
    product_code: Optional[str] = None
    quantity_delivered: Decimal
    quantity_accepted: Decimal = Decimal("0.000")
    quantity_rejected: Decimal = Decimal("0.000")


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating DN line."""

    po_line_id: Optional[uuid.UUID] = None


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """DN line response schema."""

    id: uuid.UUID
    po_line_id: Optional[uuid.UUID] = None


class DeliveryNoteBase(BaseSchema):
    """Base delivery note schema."""

    vendor_id: uuid.UUID
    vendor_name: str
    vendor_code: Optional[str] = None
    purchase_order_id: Optional[uuid.UUID] = None
    po_number: Optional[str] = None
    dn_number: str
    dn_date: str
    received_date: Optional[str] = None
    notes: Optional[str] = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating a delivery note."""

    lines: List[DeliveryNoteLineCreate]
    source_system: str = "warehouse"


class DeliveryNoteResponse(DeliveryNoteBase):
    """Delivery note response schema."""

    id: uuid.UUID
    status: str
    source_system: str
    created_at: datetime
    updated_at: datetime
    lines: List[DeliveryNoteLineResponse] = []


# Matching Schemas
class MatchScore(BaseSchema):
    """Match score breakdown."""

    total: float
    price_score: Optional[float] = None
    quantity_score: Optional[float] = None
    delivery_score: Optional[float] = None
    description_score: Optional[float] = None


class MatchRecordResponse(BaseSchema):
    """Match record response schema."""

    id: uuid.UUID
    invoice_id: uuid.UUID
    purchase_order_id: Optional[uuid.UUID] = None
    delivery_note_id: Optional[uuid.UUID] = None
    match_score: float
    score_breakdown: Optional[MatchScore] = None
    decision: str
    status: str
    matched_at: str
    confirmed_at: Optional[str] = None
    confirmed_by: Optional[str] = None


class MatchingTriggerRequest(BaseSchema):
    """Request to trigger matching for an invoice."""

    invoice_id: uuid.UUID
    force_rematch: bool = False


class MatchingResultResponse(BaseSchema):
    """Response from matching operation."""

    invoice_id: uuid.UUID
    status: str
    match_record: Optional[MatchRecordResponse] = None
    exceptions: List["ExceptionResponse"] = []
    auto_action: Optional[str] = None


# Exception Schemas
class ExceptionBase(BaseSchema):
    """Base exception schema."""

    exception_type: str
    severity: str = "medium"
    description: str
    details: Optional[str] = None
    price_variance: Optional[Decimal] = None
    quantity_variance: Optional[Decimal] = None
    variance_percentage: Optional[float] = None


class ExceptionResponse(ExceptionBase):
    """Exception response schema."""

    id: uuid.UUID
    invoice_id: uuid.UUID
    match_record_id: Optional[uuid.UUID] = None
    status: str
    resolution: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[str] = None
    resolution_notes: Optional[str] = None
    created_at: datetime


class ExceptionResolveRequest(BaseSchema):
    """Request to resolve an exception."""

    resolution: str
    notes: Optional[str] = None
    adjusted_amount: Optional[Decimal] = None
    adjusted_quantity: Optional[Decimal] = None


class ExceptionDismissRequest(BaseSchema):
    """Request to dismiss an exception."""

    reason: str


# Balance Schemas
class BalanceEntryResponse(BaseSchema):
    """Balance ledger entry response."""

    id: uuid.UUID
    po_line_id: uuid.UUID
    transaction_type: str
    transaction_reference: str
    quantity_before: Decimal
    quantity_change: Decimal
    quantity_after: Decimal
    amount_before: Decimal
    amount_change: Decimal
    amount_after: Decimal
    created_at: datetime


class BalanceSummaryResponse(BaseSchema):
    """Balance summary for a PO line."""

    po_line_id: uuid.UUID
    quantity_ordered: Decimal
    quantity_delivered: Decimal
    quantity_invoiced: Decimal
    quantity_credited: Decimal
    quantity_balance: Decimal
    amount_ordered: Decimal
    amount_delivered: Decimal
    amount_invoiced: Decimal
    amount_credited: Decimal
    amount_balance: Decimal
    delivery_percentage: Decimal
    invoice_percentage: Decimal


# Cross Reference Schemas
class CrossReferenceResponse(BaseSchema):
    """Cross reference response schema."""

    id: uuid.UUID
    vendor_id: uuid.UUID
    product_code: Optional[str] = None
    po_line_description: str
    invoice_line_description: str
    description_match_score: float
    confidence: str
    status: str
    match_count: int
    success_count: int
    success_rate: Decimal
    last_match_at: Optional[str] = None


# Update forward references
MatchingResultResponse.model_rebuild()

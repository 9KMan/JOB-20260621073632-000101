// api/schemas.py
"""Shared Pydantic schemas for API request/response models.

This module defines all Pydantic models used across the API for
validation and serialization.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generic, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# Generic type for list responses
T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""

    created_at: datetime
    updated_at: datetime


# ============================================================================
# Common Response Wrappers
# ============================================================================


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

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


class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""

    success: bool = True
    message: Optional[str] = None
    data: Optional[T] = None


class ErrorResponse(BaseModel):
    """Error response model."""

    success: bool = False
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


# ============================================================================
# Invoice Schemas
# ============================================================================


class InvoiceLineCreate(BaseSchema):
    """Schema for creating invoice line items."""

    line_number: int
    description: str = Field(..., min_length=1, max_length=500)
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    unit_of_measure: Optional[str] = None
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    line_amount: Decimal = Field(..., ge=0)


class InvoiceLineResponse(BaseSchema):
    """Schema for invoice line response."""

    id: str
    line_number: int
    description: str
    product_code: Optional[str]
    product_name: Optional[str]
    unit_of_measure: Optional[str]
    quantity: Decimal
    unit_price: Decimal
    line_amount: Decimal
    status: str
    matched_quantity: Decimal
    created_at: datetime
    updated_at: datetime


class InvoiceCreate(BaseSchema):
    """Schema for creating invoices."""

    invoice_number: str = Field(..., min_length=1, max_length=100)
    vendor_number: str = Field(..., min_length=1, max_length=50)
    vendor_name: Optional[str] = None
    invoice_date: date
    due_date: Optional[date] = None
    subtotal: Decimal = Field(..., ge=0)
    tax_amount: Decimal = Field(..., ge=0)
    total_amount: Decimal = Field(..., ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    tax_id: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    payment_terms: Optional[str] = None
    lines: list[InvoiceLineCreate] = Field(..., min_length=1)


class InvoiceUpdate(BaseSchema):
    """Schema for updating invoices."""

    vendor_name: Optional[str] = None
    due_date: Optional[date] = None
    tax_id: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    payment_terms: Optional[str] = None


class InvoiceResponse(BaseSchema):
    """Schema for invoice response."""

    id: str
    invoice_number: str
    vendor_number: str
    vendor_name: Optional[str]
    invoice_date: date
    due_date: Optional[date]
    received_date: datetime
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    currency: str
    status: str
    match_decision: Optional[str]
    match_confidence: Optional[str]
    match_score: Optional[Decimal]
    match_decision_at: Optional[datetime]
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    rejected_by: Optional[str]
    rejected_at: Optional[datetime]
    rejection_reason: Optional[str]
    created_at: datetime
    updated_at: datetime
    lines: list[InvoiceLineResponse]


class InvoiceListResponse(BaseSchema):
    """Schema for invoice list response (without lines)."""

    id: str
    invoice_number: str
    vendor_number: str
    vendor_name: Optional[str]
    invoice_date: date
    total_amount: Decimal
    currency: str
    status: str
    match_decision: Optional[str]
    created_at: datetime


# ============================================================================
# Purchase Order Schemas
# ============================================================================


class POLineCreate(BaseSchema):
    """Schema for creating PO line items."""

    line_number: int
    description: str = Field(..., min_length=1, max_length=500)
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    unit_of_measure: Optional[str] = None
    quantity_ordered: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    line_amount: Decimal = Field(..., ge=0)


class POLineResponse(BaseSchema):
    """Schema for PO line response."""

    id: str
    line_number: int
    description: str
    product_code: Optional[str]
    product_name: Optional[str]
    unit_of_measure: Optional[str]
    quantity_ordered: Decimal
    quantity_received: Decimal
    quantity_invoiced: Decimal
    unit_price: Decimal
    line_amount: Decimal
    status: str
    expected_delivery_date: Optional[date]
    created_at: datetime
    updated_at: datetime


class PurchaseOrderCreate(BaseSchema):
    """Schema for creating purchase orders."""

    po_number: str = Field(..., min_length=1, max_length=50)
    vendor_number: str = Field(..., min_length=1, max_length=50)
    vendor_name: Optional[str] = None
    po_date: date
    delivery_date: Optional[date] = None
    expected_delivery_date: Optional[date] = None
    subtotal: Decimal = Field(..., ge=0)
    tax_amount: Decimal = Field(..., ge=0)
    total_amount: Decimal = Field(..., ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    buyer_name: Optional[str] = None
    department: Optional[str] = None
    payment_terms: Optional[str] = None
    shipping_terms: Optional[str] = None
    notes: Optional[str] = None
    lines: list[POLineCreate] = Field(..., min_length=1)


class PurchaseOrderResponse(BaseSchema):
    """Schema for purchase order response."""

    id: str
    po_number: str
    vendor_number: str
    vendor_name: Optional[str]
    po_date: date
    delivery_date: Optional[date]
    expected_delivery_date: Optional[date]
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    currency: str
    status: str
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    buyer_name: Optional[str]
    department: Optional[str]
    payment_terms: Optional[str]
    shipping_terms: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    lines: list[POLineResponse]


class PurchaseOrderListResponse(BaseSchema):
    """Schema for PO list response (without lines)."""

    id: str
    po_number: str
    vendor_number: str
    vendor_name: Optional[str]
    po_date: date
    total_amount: Decimal
    currency: str
    status: str
    created_at: datetime


# ============================================================================
# Delivery Note Schemas
# ============================================================================


class DeliveryNoteLineCreate(BaseSchema):
    """Schema for creating delivery note line items."""

    line_number: int
    description: str = Field(..., min_length=1, max_length=500)
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    unit_of_measure: Optional[str] = None
    quantity_delivered: Decimal = Field(..., gt=0)


class DeliveryNoteLineResponse(BaseSchema):
    """Schema for delivery note line response."""

    id: str
    line_number: int
    description: str
    product_code: Optional[str]
    product_name: Optional[str]
    unit_of_measure: Optional[str]
    quantity_delivered: Decimal
    quantity_received: Decimal
    quantity_invoiced: Decimal
    status: str
    created_at: datetime
    updated_at: datetime


class DeliveryNoteCreate(BaseSchema):
    """Schema for creating delivery notes."""

    dn_number: str = Field(..., min_length=1, max_length=50)
    po_number: Optional[str] = None
    vendor_number: str = Field(..., min_length=1, max_length=50)
    vendor_name: Optional[str] = None
    dn_date: date
    received_date: Optional[date] = None
    source_system: Optional[str] = None
    source_id: Optional[str] = None
    notes: Optional[str] = None
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    lines: list[DeliveryNoteLineCreate] = Field(..., min_length=1)


class DeliveryNoteResponse(BaseSchema):
    """Schema for delivery note response."""

    id: str
    dn_number: str
    po_number: Optional[str]
    vendor_number: str
    vendor_name: Optional[str]
    dn_date: date
    received_date: Optional[date]
    status: str
    source_system: Optional[str]
    source_id: Optional[str]
    notes: Optional[str]
    carrier: Optional[str]
    tracking_number: Optional[str]
    created_at: datetime
    updated_at: datetime
    lines: list[DeliveryNoteLineResponse]


class DeliveryNoteListResponse(BaseSchema):
    """Schema for delivery note list response."""

    id: str
    dn_number: str
    po_number: Optional[str]
    vendor_number: str
    vendor_name: Optional[str]
    dn_date: date
    status: str
    created_at: datetime


# ============================================================================
# Matching Schemas
# ============================================================================


class MatchTriggerRequest(BaseSchema):
    """Schema for triggering matching."""

    invoice_id: str
    force_rematch: bool = False


class MatchLineResult(BaseSchema):
    """Schema for individual line match result."""

    invoice_line_id: str
    po_line_id: Optional[str]
    dn_line_id: Optional[str]
    match_type: str
    match_score: Decimal
    invoice_quantity: Decimal
    po_quantity: Optional[Decimal]
    dn_quantity: Optional[Decimal]
    price_variance: Optional[Decimal]
    quantity_variance: Optional[Decimal]


class MatchResult(BaseSchema):
    """Schema for complete match result."""

    invoice_id: str
    decision: str
    confidence: str
    score: Decimal
    total_lines: int
    matched_lines: int
    unmatched_lines: int
    exceptions: list[str]
    line_results: list[MatchLineResult]


class MatchDecisionRequest(BaseSchema):
    """Schema for user match decision."""

    invoice_id: str
    decision: str = Field(..., pattern="^(approve|reject)$")
    notes: Optional[str] = None


# ============================================================================
# Exception Schemas
# ============================================================================


class ExceptionResponse(BaseSchema):
    """Schema for exception response."""

    id: str
    invoice_id: str
    invoice_line_id: Optional[str]
    exception_type: str
    severity: str
    expected_value: Optional[Decimal]
    actual_value: Optional[Decimal]
    variance_amount: Optional[Decimal]
    variance_percentage: Optional[Decimal]
    status: str
    resolution: Optional[str]
    resolved_by: Optional[str]
    resolved_at: Optional[datetime]
    reviewed_by: Optional[str]
    reviewed_at: Optional[datetime]
    escalated_to: Optional[str]
    created_at: datetime
    updated_at: datetime


class ExceptionResolveRequest(BaseSchema):
    """Schema for resolving an exception."""

    resolution: str = Field(..., min_length=1)
    adjust_values: bool = False


class ExceptionDismissRequest(BaseSchema):
    """Schema for dismissing an exception."""

    reason: str = Field(..., min_length=1)


# ============================================================================
# Balance Ledger Schemas
# ============================================================================


class BalanceLedgerResponse(BaseSchema):
    """Schema for balance ledger response."""

    id: str
    po_line_id: str
    document_type: str
    document_id: str
    document_number: str
    quantity_balance: Decimal
    amount_balance: Decimal
    original_quantity: Decimal
    original_amount: Decimal
    total_delivered: Decimal
    total_invoiced: Decimal
    is_active: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class BalanceSummaryResponse(BaseSchema):
    """Schema for balance summary across PO lines."""

    po_id: str
    po_number: str
    total_ordered: Decimal
    total_delivered: Decimal
    total_invoiced: Decimal
    total_balance: Decimal
    line_balances: list[BalanceLedgerResponse]


# ============================================================================
# Cross Reference Schemas
# ============================================================================


class CrossRefResponse(BaseSchema):
    """Schema for cross reference response."""

    id: str
    match_key: str
    invoice_vendor_number: str
    invoice_product_code: Optional[str]
    invoice_product_name: Optional[str]
    invoice_unit_price: Optional[Decimal]
    po_vendor_number: str
    po_product_code: Optional[str]
    po_product_name: Optional[str]
    po_unit_price: Optional[Decimal]
    match_count: int
    last_match_score: Decimal
    avg_match_score: Decimal
    confidence_level: str
    is_promoted: bool
    is_active: bool
    confirmed_by: Optional[str]
    confirmed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Authentication Schemas
# ============================================================================


class Token(BaseSchema):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseSchema):
    """JWT token payload."""

    sub: str
    exp: datetime
    iat: datetime
    role: Optional[str] = None


class UserCreate(BaseSchema):
    """Schema for user creation."""

    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=8)
    role: Optional[str] = "user"


class UserResponse(BaseSchema):
    """Schema for user response."""

    id: str
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

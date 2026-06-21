// src/schemas/invoice.py
"""Invoice schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.common import BaseSchema, PaginatedResponse


class InvoiceLineBase(BaseSchema):
    """Base schema for invoice line items."""

    line_number: int = Field(..., ge=1)
    product_code: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    quantity: Decimal = Field(..., ge=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=0)
    line_total: Decimal = Field(..., ge=0)
    tax_rate: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    tax_amount: Decimal = Field(default=Decimal("0"), ge=0)
    matched_quantity: Decimal = Field(default=Decimal("0"), ge=0)
    notes: Optional[str] = None


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating invoice line items."""

    pass


class InvoiceLineUpdate(BaseSchema):
    """Schema for updating invoice line items."""

    line_number: Optional[int] = Field(None, ge=1)
    product_code: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    quantity: Optional[Decimal] = Field(None, ge=0)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    line_total: Optional[Decimal] = Field(None, ge=0)
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    matched_quantity: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None


class InvoiceLineResponse(InvoiceLineBase):
    """Schema for invoice line item responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    invoice_id: UUID
    created_at: datetime
    updated_at: datetime


class InvoiceBase(BaseSchema):
    """Base schema for Invoices."""

    invoice_number: str = Field(..., max_length=50)
    purchase_order_id: Optional[UUID] = None
    supplier_id: UUID
    supplier_name: str = Field(..., max_length=255)
    supplier_code: Optional[str] = Field(None, max_length=50)
    invoice_date: date
    due_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    subtotal: Decimal = Field(default=Decimal("0"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0"), ge=0)
    total_amount: Decimal = Field(default=Decimal("0"), ge=0)
    status: str = Field(default="draft", max_length=30)
    match_status: str = Field(default="pending", max_length=20)
    match_confidence: Optional[Decimal] = None
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating Invoices."""

    lines: List[InvoiceLineCreate] = Field(default_factory=list)


class InvoiceUpdate(BaseSchema):
    """Schema for updating Invoices."""

    purchase_order_id: Optional[UUID] = None
    supplier_name: Optional[str] = Field(None, max_length=255)
    supplier_code: Optional[str] = Field(None, max_length=50)
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    currency: Optional[str] = Field(None, max_length=3)
    subtotal: Optional[Decimal] = Field(None, ge=0)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    total_amount: Optional[Decimal] = Field(None, ge=0)
    status: Optional[str] = Field(None, max_length=30)
    match_status: Optional[str] = Field(None, max_length=20)
    match_confidence: Optional[Decimal] = None
    notes: Optional[str] = None


class InvoiceResponse(InvoiceBase):
    """Schema for Invoice responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    deleted_at: Optional[datetime] = None
    matched_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    lines: List[InvoiceLineResponse] = Field(default_factory=list)


class InvoiceListResponse(PaginatedResponse[InvoiceResponse]):
    """Schema for paginated Invoice list response."""

    pass


class InvoiceSummary(BaseSchema):
    """Schema for Invoice summary (minimal data)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    invoice_number: str
    supplier_name: str
    total_amount: Decimal
    status: str
    match_status: str
    invoice_date: date


class InvoiceMatchRequest(BaseSchema):
    """Schema for requesting invoice matching."""

    auto_match: bool = Field(default=True, description="Auto-match with PO and DN if possible")
    variance_tolerance: Decimal = Field(
        default=Decimal("5.00"),
        ge=0,
        le=100,
        description="Variance tolerance percentage",
    )

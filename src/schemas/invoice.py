// src/schemas/invoice.py
"""Invoice schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.base import BaseSchema, PaginatedResponse


class InvoiceLineBase(BaseModel):
    """Base schema for Invoice line items."""

    line_number: int
    sku: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=0)
    line_amount: Decimal = Field(..., ge=0)
    tax_rate: Decimal = Field(default=Decimal("0.00"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating Invoice line items."""

    po_line_id: Optional[UUID] = None
    delivery_note_line_id: Optional[UUID] = None


class InvoiceLineResponse(InvoiceLineBase):
    """Schema for Invoice line item response."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    invoice_id: UUID
    po_line_id: Optional[UUID] = None
    delivery_note_line_id: Optional[UUID] = None
    matched_quantity: Decimal
    created_at: datetime
    updated_at: datetime


class InvoiceBase(BaseModel):
    """Base schema for Invoices."""

    invoice_number: str = Field(..., max_length=100)
    supplier_id: UUID
    supplier_name: str = Field(..., max_length=255)
    supplier_reference: Optional[str] = Field(None, max_length=100)
    purchase_order_id: Optional[UUID] = None
    invoice_date: date
    due_date: Optional[date] = None
    received_date: Optional[date] = None
    subtotal: Decimal = Field(..., ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    total_amount: Decimal = Field(..., ge=0)
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating an Invoice."""

    lines: list[InvoiceLineCreate] = Field(default_factory=list)


class InvoiceUpdate(BaseModel):
    """Schema for updating an Invoice."""

    supplier_name: Optional[str] = Field(None, max_length=255)
    due_date: Optional[date] = None
    notes: Optional[str] = None
    status: Optional[str] = Field(None, max_length=20)
    lines: Optional[list[InvoiceLineCreate]] = None


class InvoiceResponse(InvoiceBase):
    """Schema for Invoice response."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    status: str
    matched_amount: Decimal
    unmatched_amount: Decimal
    lines: list[InvoiceLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class InvoiceListResponse(PaginatedResponse[InvoiceResponse]):
    """Paginated list of Invoices."""

    pass

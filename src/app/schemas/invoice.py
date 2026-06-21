// src/app/schemas/invoice.py
"""Invoice schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class InvoiceLineBase(BaseModel):
    """Base invoice line schema."""

    line_number: int = Field(..., ge=1)
    description: str = Field(..., min_length=1, max_length=500)
    sku: Optional[str] = Field(None, max_length=100)
    quantity: Decimal = Field(..., ge=0)
    unit_price: Decimal = Field(..., ge=0)
    line_total: Decimal = Field(..., ge=0)
    uom: str = Field(default="EA", max_length=20)
    tax_rate: Decimal = Field(default=Decimal("0"), ge=0)


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating an invoice line."""

    pass


class InvoiceLineUpdate(BaseModel):
    """Schema for updating an invoice line."""

    line_number: Optional[int] = Field(None, ge=1)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    sku: Optional[str] = Field(None, max_length=100)
    quantity: Optional[Decimal] = Field(None, ge=0)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    line_total: Optional[Decimal] = Field(None, ge=0)
    uom: Optional[str] = Field(None, max_length=20)
    tax_rate: Optional[Decimal] = Field(None, ge=0)


class InvoiceLineResponse(InvoiceLineBase):
    """Invoice line response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    invoice_id: UUID
    created_at: datetime
    updated_at: datetime


class InvoiceBase(BaseModel):
    """Base invoice schema."""

    invoice_number: str = Field(..., min_length=1, max_length=100)
    supplier_id: UUID
    purchase_order_id: Optional[UUID] = None
    invoice_date: date
    due_date: Optional[date] = None
    status: str = Field(default="RECEIVED", max_length=50)
    total_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    subtotal: Decimal = Field(default=Decimal("0.00"), ge=0)
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None
    attachment_url: Optional[str] = Field(None, max_length=500)


class InvoiceCreate(InvoiceBase):
    """Schema for creating an invoice."""

    lines: list[InvoiceLineCreate] = []


class InvoiceUpdate(BaseModel):
    """Schema for updating an invoice."""

    invoice_number: Optional[str] = Field(None, min_length=1, max_length=100)
    supplier_id: Optional[UUID] = None
    purchase_order_id: Optional[UUID] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    status: Optional[str] = Field(None, max_length=50)
    total_amount: Optional[Decimal] = Field(None, ge=0)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    subtotal: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    notes: Optional[str] = None
    attachment_url: Optional[str] = Field(None, max_length=500)
    lines: Optional[list[InvoiceLineCreate]] = None


class InvoiceResponse(InvoiceBase):
    """Invoice response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class InvoiceDetailResponse(InvoiceResponse):
    """Invoice detail response with lines."""

    lines: list[InvoiceLineResponse] = []
    supplier_name: Optional[str] = None
    supplier_code: Optional[str] = None
    po_number: Optional[str] = None


class InvoiceListResponse(BaseModel):
    """Schema for invoice list response."""

    items: list[InvoiceDetailResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

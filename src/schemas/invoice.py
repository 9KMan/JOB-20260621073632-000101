// src/schemas/invoice.py
"""Invoice schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class InvoiceLineBase(BaseModel):
    """Base schema for invoice line."""
    line_number: int
    sku: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    line_total: Decimal = Field(..., ge=0)


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating an invoice line."""
    pass


class InvoiceLineResponse(InvoiceLineBase):
    """Schema for invoice line response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    invoice_id: UUID
    created_at: datetime
    updated_at: datetime


class InvoiceLineUpdate(BaseModel):
    """Schema for updating an invoice line."""
    sku: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit_price: Optional[Decimal] = Field(None, ge=0)


class InvoiceBase(BaseModel):
    """Base schema for Invoice."""
    invoice_number: str = Field(..., max_length=100)
    supplier_id: str = Field(..., max_length=100)
    supplier_name: str = Field(..., max_length=255)
    po_reference: Optional[str] = Field(None, max_length=100)
    currency: str = Field(default="USD", max_length=3)
    subtotal: Decimal = Field(..., ge=0)
    tax_amount: Decimal = Field(default=Decimal("0"), ge=0)
    total_amount: Decimal = Field(..., ge=0)
    invoice_date: date
    due_date: Optional[date] = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating an Invoice."""
    lines: list[InvoiceLineCreate] = Field(default_factory=list)


class InvoiceUpdate(BaseModel):
    """Schema for updating an Invoice."""
    supplier_id: Optional[str] = Field(None, max_length=100)
    supplier_name: Optional[str] = Field(None, max_length=255)
    po_reference: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, max_length=50)
    currency: Optional[str] = Field(None, max_length=3)
    subtotal: Optional[Decimal] = Field(None, ge=0)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    total_amount: Optional[Decimal] = Field(None, ge=0)
    due_date: Optional[date] = None


class InvoiceResponse(InvoiceBase):
    """Schema for Invoice response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    lines: list[InvoiceLineResponse] = Field(default_factory=list)


class InvoiceListResponse(BaseModel):
    """Schema for paginated invoice list."""
    items: list[InvoiceResponse]
    total: int
    page: int
    page_size: int
    pages: int

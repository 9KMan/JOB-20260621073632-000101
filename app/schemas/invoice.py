# app/schemas/invoice.py
"""Invoice schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class InvoiceLineBase(BaseModel):
    """Base invoice line schema."""

    line_number: int = Field(..., ge=1)
    product_code: Optional[str] = Field(None, max_length=100)
    description: str = Field(..., min_length=1)
    quantity: Decimal = Field(..., ge=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=0)
    tax_rate: Decimal = Field(default=Decimal("0"), ge=0, le=1)


class InvoiceLineCreate(InvoiceLineBase):
    """Invoice line creation request."""

    pass


class InvoiceLineResponse(InvoiceLineBase):
    """Invoice line response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    line_total: Decimal
    created_at: datetime
    updated_at: datetime


class InvoiceBase(BaseModel):
    """Base invoice schema."""

    invoice_number: str = Field(..., min_length=1, max_length=50)
    vendor_id: str
    vendor_invoice_number: Optional[str] = Field(None, max_length=100)
    po_reference: Optional[str] = Field(None, max_length=50)
    invoice_date: str
    due_date: Optional[str] = None
    currency: str = Field(default="USD", max_length=3)
    shipping_cost: Decimal = Field(default=Decimal("0"), ge=0)
    notes: Optional[str] = None
    raw_data: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    """Invoice creation request."""

    lines: List[InvoiceLineCreate]
    status: str = Field(default="submitted")


class InvoiceUpdate(BaseModel):
    """Invoice update request."""

    invoice_number: Optional[str] = Field(None, min_length=1, max_length=50)
    vendor_id: Optional[str] = None
    vendor_invoice_number: Optional[str] = Field(None, max_length=100)
    po_reference: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    currency: Optional[str] = Field(None, max_length=3)
    shipping_cost: Optional[Decimal] = Field(None, ge=0)
    amount_paid: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None
    raw_data: Optional[str] = None


class InvoiceResponse(InvoiceBase):
    """Invoice response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    amount_paid: Decimal
    created_at: datetime
    updated_at: datetime
    lines: List[InvoiceLineResponse] = []


class InvoiceListResponse(BaseModel):
    """Invoice list response with pagination."""

    items: List[InvoiceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

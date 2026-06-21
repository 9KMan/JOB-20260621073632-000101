// src/app/schemas/invoice.py
"""Invoice Pydantic schemas."""

from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field

from src.app.schemas.supplier import SupplierResponse


class InvoiceLineBase(BaseModel):
    """Base invoice line schema."""

    line_number: int = Field(..., ge=1)
    item_code: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    line_total: Decimal = Field(..., ge=0)
    tax_rate: Optional[Decimal] = Field(None, ge=0)
    uom: Optional[str] = Field(None, max_length=20)


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating an invoice line."""

    pass


class InvoiceLineResponse(InvoiceLineBase):
    """Schema for invoice line response."""

    id: str
    invoice_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InvoiceBase(BaseModel):
    """Base invoice schema."""

    invoice_number: str = Field(..., min_length=1, max_length=50)
    po_reference: Optional[str] = Field(None, max_length=50)
    supplier_id: str
    invoice_date: date
    due_date: Optional[date] = None
    total_amount: Decimal = Field(..., ge=0)
    tax_amount: Decimal = Field(..., ge=0)
    currency: str = Field(default="USD", max_length=3)
    status: str = Field(default="PENDING", max_length=20)
    payment_status: str = Field(default="UNPAID", max_length=20)
    notes: Optional[str] = Field(None, max_length=1000)


class InvoiceCreate(InvoiceBase):
    """Schema for creating an invoice."""

    lines: List[InvoiceLineCreate] = Field(..., min_length=1)


class InvoiceUpdate(BaseModel):
    """Schema for updating an invoice."""

    due_date: Optional[date] = None
    status: Optional[str] = Field(None, max_length=20)
    payment_status: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = Field(None, max_length=1000)


class InvoiceResponse(InvoiceBase):
    """Schema for invoice response."""

    id: str
    created_at: datetime
    updated_at: datetime
    lines: List[InvoiceLineResponse] = []
    supplier: Optional[SupplierResponse] = None

    class Config:
        from_attributes = True


class InvoiceListResponse(BaseModel):
    """Schema for paginated invoice list response."""

    items: List[InvoiceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

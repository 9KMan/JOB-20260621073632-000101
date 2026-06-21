// src/app/schemas/invoice.py
"""
Invoice schemas.
"""
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field

from app.schemas.common import BaseSchema, TimestampMixin
from app.schemas.supplier import SupplierResponse


class InvoiceLineBase(BaseModel):
    """Base invoice line schema."""
    line_number: int = Field(..., ge=1)
    product_code: Optional[str] = Field(default=None, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=0)
    line_total: Decimal


class InvoiceLineCreate(InvoiceLineBase):
    """Invoice line creation schema."""
    pass


class InvoiceLineResponse(InvoiceLineBase, TimestampMixin):
    """Invoice line response schema."""
    id: str
    invoice_id: str


class InvoiceBase(BaseModel):
    """Base invoice schema."""
    invoice_number: str = Field(..., min_length=1, max_length=50)
    supplier_id: str
    po_reference: Optional[str] = Field(default=None, max_length=50)
    invoice_date: date
    due_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None
    erp_reference: Optional[str] = Field(default=None, max_length=100)


class InvoiceCreate(InvoiceBase):
    """Invoice creation schema."""
    lines: List[InvoiceLineCreate]
    subtotal: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None


class InvoiceUpdate(BaseModel):
    """Invoice update schema."""
    invoice_number: Optional[str] = Field(default=None, min_length=1, max_length=50)
    supplier_id: Optional[str] = None
    po_reference: Optional[str] = Field(default=None, max_length=50)
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    status: Optional[str] = None
    payment_status: Optional[str] = None
    notes: Optional[str] = None
    erp_reference: Optional[str] = Field(default=None, max_length=100)


class InvoiceResponse(InvoiceBase, TimestampMixin):
    """Invoice response schema."""
    id: str
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    payment_status: str
    paid_date: Optional[datetime] = None
    paid_amount: Decimal
    supplier: Optional[SupplierResponse] = None
    lines: List[InvoiceLineResponse] = []
    is_paid: bool = False

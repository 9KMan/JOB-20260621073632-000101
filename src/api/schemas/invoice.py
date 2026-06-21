// src/api/schemas/invoice.py
"""Invoice schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field


class InvoiceLineCreate(BaseModel):
    """Invoice line creation schema."""
    line_number: int = Field(..., gt=0)
    item_code: str = Field(..., max_length=50)
    item_description: str = Field(..., max_length=500)
    quantity_invoiced: Decimal = Field(..., gt=0, decimal_places=3)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=0, decimal_places=4)
    line_total: Decimal = Field(..., ge=0, decimal_places=2)


class InvoiceLineResponse(BaseModel):
    """Invoice line response."""
    id: str
    invoice_id: str
    line_number: int
    item_code: str
    item_description: str
    quantity_invoiced: Decimal
    unit_of_measure: str
    unit_price: Decimal
    line_total: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


class InvoiceCreate(BaseModel):
    """Invoice creation schema."""
    invoice_number: str = Field(..., max_length=50)
    supplier_code: str = Field(..., max_length=50)
    supplier_name: str = Field(..., max_length=255)
    invoice_date: date
    due_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    subtotal: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)
    total_amount: Decimal = Field(..., ge=0, decimal_places=2)
    notes: Optional[str] = Field(None, max_length=1000)
    lines: List[InvoiceLineCreate]


class InvoiceUpdate(BaseModel):
    """Invoice update schema."""
    supplier_code: Optional[str] = Field(None, max_length=50)
    supplier_name: Optional[str] = Field(None, max_length=255)
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    currency: Optional[str] = Field(None, max_length=3)
    subtotal: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    tax_amount: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    total_amount: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    status: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = Field(None, max_length=1000)


class InvoiceResponse(BaseModel):
    """Invoice response."""
    id: str
    invoice_number: str
    supplier_code: str
    supplier_name: str
    invoice_date: date
    due_date: Optional[date] = None
    currency: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    status: str
    is_deleted: bool
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    lines: List[InvoiceLineResponse] = []

    class Config:
        from_attributes = True

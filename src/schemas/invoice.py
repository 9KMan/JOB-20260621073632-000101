# src/schemas/invoice.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


class InvoiceLineBase(BaseModel):
    """Base schema for Invoice line."""
    line_number: int = Field(..., ge=1)
    product_code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=0)
    tax_rate: Decimal = Field(default=Decimal("0"))
    po_line_reference: Optional[str] = Field(None, max_length=36)
    notes: Optional[str] = Field(None, max_length=500)


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating Invoice line."""
    tax_amount: Optional[Decimal] = None


class InvoiceLineUpdate(BaseModel):
    """Schema for updating Invoice line."""
    line_number: Optional[int] = Field(None, ge=1)
    product_code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    tax_rate: Optional[Decimal] = None
    po_line_reference: Optional[str] = Field(None, max_length=36)
    notes: Optional[str] = Field(None, max_length=500)


class InvoiceLineResponse(InvoiceLineBase):
    """Schema for Invoice line response."""
    id: str
    invoice_id: str
    line_amount: Decimal
    tax_amount: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InvoiceBase(BaseModel):
    """Base schema for Invoice."""
    invoice_number: str = Field(..., max_length=50)
    supplier_id: str = Field(..., max_length=36)
    supplier_name: str = Field(..., max_length=255)
    supplier_code: Optional[str] = Field(None, max_length=50)
    invoice_date: date
    due_date: Optional[date] = None
    po_reference: Optional[str] = Field(None, max_length=50)
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = Field(None, max_length=1000)
    metadata: Optional[str] = Field(None, max_length=5000)


class InvoiceCreate(InvoiceBase):
    """Schema for creating Invoice."""
    lines: List[InvoiceLineCreate] = Field(default_factory=list)


class InvoiceUpdate(BaseModel):
    """Schema for updating Invoice."""
    supplier_name: Optional[str] = Field(None, max_length=255)
    supplier_code: Optional[str] = Field(None, max_length=50)
    due_date: Optional[date] = None
    po_reference: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=1000)
    metadata: Optional[str] = Field(None, max_length=5000)


class InvoiceResponse(InvoiceBase):
    """Schema for Invoice response."""
    id: str
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    amount_paid: Decimal
    created_at: datetime
    updated_at: datetime
    lines: List[InvoiceLineResponse] = []

    class Config:
        from_attributes = True

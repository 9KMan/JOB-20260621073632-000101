// src/app/schemas/invoice.py
"""Invoice Pydantic schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class InvoiceLineBase(BaseModel):
    """Base invoice line schema."""
    line_number: int = Field(..., ge=1)
    item_code: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., min_length=1, max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=0)
    tax_rate: Decimal = Field(default=Decimal("0.00"), ge=0)


class InvoiceLineCreate(InvoiceLineBase):
    """Invoice line creation schema."""
    po_line_id: Optional[UUID] = None
    dn_line_id: Optional[UUID] = None


class InvoiceLineUpdate(BaseModel):
    """Invoice line update schema."""
    item_code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    tax_rate: Optional[Decimal] = Field(None, ge=0)
    po_line_id: Optional[UUID] = None
    dn_line_id: Optional[UUID] = None


class InvoiceLineResponse(InvoiceLineBase):
    """Invoice line response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    invoice_id: UUID
    po_line_id: Optional[UUID] = None
    dn_line_id: Optional[UUID] = None
    line_amount: Decimal
    tax_amount: Decimal
    created_at: datetime
    updated_at: datetime


class InvoiceBase(BaseModel):
    """Base invoice schema."""
    invoice_number: str = Field(..., min_length=1, max_length=50)
    supplier_id: UUID
    supplier_name: str = Field(..., min_length=1, max_length=255)
    po_id: Optional[UUID] = None
    po_number: Optional[str] = Field(None, max_length=50)
    invoice_date: date
    due_date: Optional[date] = None
    payment_terms: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    currency: str = Field(default="USD", max_length=3)


class InvoiceCreate(InvoiceBase):
    """Invoice creation schema."""
    lines: List[InvoiceLineCreate] = Field(..., min_length=1)
    status: str = Field(default="pending", max_length=20)


class InvoiceUpdate(BaseModel):
    """Invoice update schema."""
    supplier_name: Optional[str] = Field(None, max_length=255)
    po_id: Optional[UUID] = None
    po_number: Optional[str] = Field(None, max_length=50)
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    payment_terms: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    status: Optional[str] = Field(None, max_length=20)


class InvoiceResponse(InvoiceBase):
    """Invoice response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    status: str
    total_amount: Decimal
    tax_amount: Decimal
    subtotal: Decimal
    matched_amount: Decimal
    open_amount: Decimal
    lines: List[InvoiceLineResponse] = []
    created_at: datetime
    updated_at: datetime

// app/schemas/invoice.py
"""Invoice schemas."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field


class InvoiceLineBase(BaseModel):
    """Base invoice line schema."""
    line_number: int = Field(..., ge=1)
    product_code: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=0)
    tax_rate: Decimal = Field(default=Decimal("0.0000"), ge=0, le=1)
    line_total: Decimal = Field(..., ge=0)


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating an invoice line."""
    pass


class InvoiceLineResponse(InvoiceLineBase):
    """Schema for invoice line response."""
    id: uuid.UUID
    invoice_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class InvoiceBase(BaseModel):
    """Base invoice schema."""
    invoice_number: str = Field(..., min_length=1, max_length=50)
    vendor_id: uuid.UUID
    po_reference: Optional[str] = Field(None, max_length=50)
    invoice_date: date
    due_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating an invoice."""
    status: str = Field(default="RECEIVED", max_length=20)
    lines: List[InvoiceLineCreate] = Field(default_factory=list)


class InvoiceUpdate(BaseModel):
    """Schema for updating an invoice."""
    vendor_id: Optional[uuid.UUID] = None
    po_reference: Optional[str] = Field(None, max_length=50)
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    status: Optional[str] = Field(None, max_length=20)
    currency: Optional[str] = Field(None, max_length=3)
    notes: Optional[str] = None
    lines: Optional[List[InvoiceLineCreate]] = None


class InvoiceResponse(InvoiceBase):
    """Schema for invoice response."""
    id: uuid.UUID
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    amount_paid: Decimal
    created_at: datetime
    updated_at: datetime
    lines: List[InvoiceLineResponse] = []
    
    model_config = {"from_attributes": True}

// api/schemas/invoice.py
"""Invoice schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


class InvoiceLineBase(BaseModel):
    """Base invoice line schema."""
    
    line_number: int = Field(..., ge=1)
    item_code: Optional[str] = Field(None, max_length=100)
    description: str = Field(..., min_length=1)
    quantity: Decimal = Field(..., gt=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=0)
    tax_rate: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating an invoice line."""
    pass


class InvoiceLineUpdate(BaseModel):
    """Schema for updating an invoice line."""
    
    item_code: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=100)


class InvoiceLineResponse(InvoiceLineBase):
    """Schema for invoice line response."""
    
    id: UUID
    invoice_id: UUID
    line_total: Decimal
    tax_amount: Decimal
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class InvoiceBase(BaseModel):
    """Base invoice schema."""
    
    invoice_number: str = Field(..., min_length=1, max_length=100)
    supplier_id: UUID
    po_id: Optional[UUID] = None
    invoice_date: date
    due_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating an invoice."""
    
    lines: List[InvoiceLineCreate] = Field(default_factory=list)


class InvoiceUpdate(BaseModel):
    """Schema for updating an invoice."""
    
    supplier_id: Optional[UUID] = None
    po_id: Optional[UUID] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    status: Optional[str] = None
    currency: Optional[str] = Field(None, max_length=3)
    notes: Optional[str] = None


class InvoiceResponse(InvoiceBase):
    """Schema for invoice response."""
    
    id: UUID
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    amount_paid: Decimal
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class InvoiceDetailResponse(InvoiceResponse):
    """Schema for detailed invoice response with lines."""
    
    lines: List[InvoiceLineResponse] = []
    
    model_config = {"from_attributes": True}

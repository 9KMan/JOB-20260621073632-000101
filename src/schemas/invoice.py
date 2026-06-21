// src/schemas/invoice.py
"""
Invoice Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal

from src.schemas.common import TimestampMixin, UUIDMixin


class InvoiceLineBase(BaseModel):
    """Base schema for Invoice line items"""
    line_number: int
    item_code: Optional[str] = None
    description: str = Field(..., max_length=500)
    quantity: Decimal = Field(..., ge=0)
    unit_of_measure: str = "EA"
    unit_price: Decimal = Field(..., ge=0)
    tax_rate: Decimal = Field(default=Decimal("0"), ge=0)
    purchase_order_line_id: Optional[UUID] = None


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating Invoice line items"""
    pass


class InvoiceLineResponse(InvoiceLineBase, UUIDMixin):
    """Response schema for Invoice line items"""
    line_amount: Decimal
    tax_amount: Decimal
    
    class Config:
        from_attributes = True


class InvoiceBase(BaseModel):
    """Base schema for Invoice"""
    invoice_number: str = Field(..., max_length=50)
    supplier_id: UUID
    supplier_name: str = Field(..., max_length=255)
    supplier_code: Optional[str] = None
    invoice_date: datetime
    due_date: Optional[datetime] = None
    currency: str = Field(default="USD", max_length=3)
    payment_terms: Optional[str] = None
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating an Invoice"""
    line_items: List[InvoiceLineCreate] = Field(default_factory=list)


class InvoiceUpdate(BaseModel):
    """Schema for updating an Invoice"""
    supplier_name: Optional[str] = None
    supplier_code: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[str] = None
    payment_terms: Optional[str] = None
    payment_reference: Optional[str] = None
    notes: Optional[str] = None


class InvoiceResponse(InvoiceBase, UUIDMixin, TimestampMixin):
    """Response schema for Invoice"""
    purchase_order_id: Optional[UUID] = None
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    status: str
    created_by: Optional[UUID] = None
    line_items: List[InvoiceLineResponse] = []
    
    class Config:
        from_attributes = True


class InvoiceListResponse(BaseModel):
    """Response schema for listing Invoices"""
    items: List[InvoiceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

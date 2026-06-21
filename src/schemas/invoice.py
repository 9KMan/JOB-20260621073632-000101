// src/schemas/invoice.py
"""Invoice schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class InvoiceLineItemBase(BaseModel):
    """Base line item schema."""
    line_number: int = Field(..., ge=1)
    item_code: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=0)
    tax_rate: Decimal = Field(default=Decimal("0.0000"), ge=0)
    line_total: Decimal = Field(..., ge=0)


class InvoiceLineItemCreate(InvoiceLineItemBase):
    """Schema for line item creation."""
    pass


class InvoiceLineItemResponse(InvoiceLineItemBase):
    """Schema for line item response."""
    id: UUID
    invoice_id: UUID
    
    model_config = {"from_attributes": True}


class InvoiceBase(BaseModel):
    """Base invoice schema."""
    invoice_number: str = Field(..., max_length=50)
    supplier_id: UUID
    purchase_order_id: Optional[UUID] = None
    invoice_date: date
    due_date: date
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    """Schema for invoice creation."""
    line_items: list[InvoiceLineItemCreate] = Field(default_factory=list)


class InvoiceUpdate(BaseModel):
    """Schema for invoice update."""
    invoice_number: Optional[str] = Field(None, max_length=50)
    supplier_id: Optional[UUID] = None
    purchase_order_id: Optional[UUID] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    status: Optional[str] = Field(None, max_length=20)
    payment_status: Optional[str] = Field(None, max_length=20)
    currency: Optional[str] = Field(None, max_length=3)
    notes: Optional[str] = None
    line_items: Optional[list[InvoiceLineItemCreate]] = None


class InvoiceResponse(InvoiceBase):
    """Schema for invoice response."""
    id: UUID
    status: str
    payment_status: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    amount_paid: Decimal
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    line_items: list[InvoiceLineItemResponse] = []
    
    model_config = {"from_attributes": True}


class InvoiceListResponse(BaseModel):
    """Schema for paginated invoice list."""
    items: list[InvoiceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

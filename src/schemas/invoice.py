# src/schemas/invoice.py
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field

from src.schemas.common import TimestampMixinSchema, UUIDMixinSchema


# Line Items
class InvoiceLineItemBase(BaseModel):
    """Base schema for invoice line items."""
    line_number: int = Field(ge=1)
    item_code: str = Field(max_length=100)
    description: str = Field(max_length=500)
    quantity: Decimal = Field(ge=0)
    unit_price: Decimal = Field(ge=0)
    line_total: Decimal = Field(ge=0)


class InvoiceLineItemCreate(InvoiceLineItemBase):
    """Schema for creating invoice line items."""
    pass


class InvoiceLineItemResponse(InvoiceLineItemBase, UUIDMixinSchema):
    """Schema for invoice line item response."""
    invoice_id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


# Invoice
class InvoiceBase(BaseModel):
    """Base schema for Invoices."""
    invoice_number: str = Field(max_length=50)
    supplier_id: str = Field(max_length=100)
    supplier_name: str = Field(max_length=255)
    invoice_date: date
    due_date: date
    subtotal: Decimal = Field(ge=0)
    tax_amount: Decimal = Field(ge=0, default=Decimal("0.00"))
    total_amount: Decimal = Field(ge=0)
    currency: str = Field(default="USD", max_length=3)
    status: str = Field(default="PENDING", max_length=20)
    notes: Optional[str] = None
    purchase_order_id: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating Invoices."""
    line_items: List[InvoiceLineItemCreate] = []


class InvoiceUpdate(BaseModel):
    """Schema for updating Invoices."""
    supplier_name: Optional[str] = None
    due_date: Optional[date] = None
    subtotal: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    purchase_order_id: Optional[str] = None


class InvoiceResponse(InvoiceBase, UUIDMixinSchema, TimestampMixinSchema):
    """Schema for Invoice response."""
    line_items: List[InvoiceLineItemResponse] = []
    
    model_config = {"from_attributes": True}

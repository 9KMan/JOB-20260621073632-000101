# src/schemas/invoice.py
"""Invoice schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class InvoiceLineBase(BaseModel):
    """Base invoice line schema."""
    line_number: int
    item_code: Optional[str] = None
    item_description: str = Field(max_length=500)
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    line_amount: Decimal = Field(ge=0)
    tax_amount: Decimal = Field(default=Decimal("0"), ge=0)
    uom: Optional[str] = None


class InvoiceLineCreate(InvoiceLineBase):
    """Invoice line creation schema."""
    pass


class InvoiceLineUpdate(BaseModel):
    """Invoice line update schema."""
    line_number: Optional[int] = None
    item_code: Optional[str] = None
    item_description: Optional[str] = None
    quantity: Optional[Decimal] = Field(default=None, gt=0)
    unit_price: Optional[Decimal] = Field(default=None, ge=0)
    line_amount: Optional[Decimal] = Field(default=None, ge=0)
    tax_amount: Optional[Decimal] = Field(default=None, ge=0)
    uom: Optional[str] = None


class InvoiceLineInDB(InvoiceLineBase):
    """Invoice line database schema."""
    id: UUID
    invoice_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoiceLineResponse(InvoiceLineBase):
    """Invoice line response schema."""
    id: UUID
    invoice_id: UUID

    model_config = ConfigDict(from_attributes=True)


class InvoiceBase(BaseModel):
    """Base invoice schema."""
    invoice_number: str = Field(max_length=100)
    supplier_id: str = Field(max_length=100)
    supplier_name: str = Field(max_length=255)
    invoice_date: date
    due_date: Optional[date] = None
    total_amount: Decimal = Field(gt=0)
    tax_amount: Decimal = Field(default=Decimal("0"), ge=0)
    net_amount: Decimal = Field(ge=0)
    currency: str = Field(default="USD", max_length=3)
    status: str = Field(default="pending", max_length=50)
    notes: Optional[str] = Field(default=None, max_length=1000)
    purchase_order_id: Optional[UUID] = None


class InvoiceCreate(InvoiceBase):
    """Invoice creation schema."""
    line_items: List[InvoiceLineCreate] = []


class InvoiceUpdate(BaseModel):
    """Invoice update schema."""
    invoice_number: Optional[str] = Field(default=None, max_length=100)
    supplier_id: Optional[str] = Field(default=None, max_length=100)
    supplier_name: Optional[str] = Field(default=None, max_length=255)
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    total_amount: Optional[Decimal] = Field(default=None, gt=0)
    tax_amount: Optional[Decimal] = Field(default=None, ge=0)
    net_amount: Optional[Decimal] = Field(default=None, ge=0)
    currency: Optional[str] = Field(default=None, max_length=3)
    status: Optional[str] = Field(default=None, max_length=50)
    notes: Optional[str] = Field(default=None, max_length=1000)
    purchase_order_id: Optional[UUID] = None
    line_items: Optional[List[InvoiceLineCreate]] = None


class InvoiceInDB(InvoiceBase):
    """Invoice database schema."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoiceResponse(InvoiceBase):
    """Invoice response schema."""
    id: UUID
    line_items: List[InvoiceLineResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoiceListResponse(BaseModel):
    """Invoice list response schema."""
    items: List[InvoiceResponse]
    total: int
    page: int
    page_size: int

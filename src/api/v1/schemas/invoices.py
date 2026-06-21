# src/api/v1/schemas/invoices.py
"""Invoice schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class InvoiceLineBase(BaseModel):
    """Base invoice line schema."""
    line_number: int
    item_code: str = Field(..., max_length=100)
    item_description: str = Field(..., max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=0)
    line_total: Decimal = Field(..., ge=0)
    tax_rate: Decimal = Field(default=Decimal("0.00"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)


class InvoiceLineCreate(InvoiceLineBase):
    """Invoice line creation schema."""
    purchase_order_line_id: Optional[UUID] = None
    delivery_note_line_id: Optional[UUID] = None


class InvoiceLineResponse(InvoiceLineBase):
    """Invoice line response schema."""
    id: UUID
    invoice_id: UUID
    purchase_order_line_id: Optional[UUID] = None
    delivery_note_line_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InvoiceBase(BaseModel):
    """Base invoice schema."""
    invoice_number: str = Field(..., max_length=50)
    supplier_id: str = Field(..., max_length=100)
    supplier_name: str = Field(..., max_length=255)
    supplier_reference: Optional[str] = Field(None, max_length=100)
    invoice_date: date
    due_date: Optional[date] = None
    po_reference: Optional[str] = Field(None, max_length=50)
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    """Invoice creation schema."""
    lines: list[InvoiceLineCreate] = Field(..., min_length=1)


class InvoiceUpdate(BaseModel):
    """Invoice update schema."""
    supplier_name: Optional[str] = Field(None, max_length=255)
    supplier_reference: Optional[str] = Field(None, max_length=100)
    due_date: Optional[date] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class InvoiceResponse(InvoiceBase):
    """Invoice response schema."""
    id: UUID
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InvoiceDetailResponse(InvoiceResponse):
    """Invoice detail response schema with lines."""
    lines: list[InvoiceLineResponse] = []

    model_config = {"from_attributes": True}

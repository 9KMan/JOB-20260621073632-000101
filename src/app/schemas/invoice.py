// src/app/schemas/invoice.py
"""Invoice schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import BaseSchema, TimestampMixin, UUIDMixin


class InvoiceLineBase(BaseModel):
    """Invoice Line base schema."""

    line_number: int = Field(ge=1)
    product_code: str = Field(max_length=100)
    product_description: str = Field(max_length=500)
    quantity: Decimal = Field(ge=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(ge=0)
    line_amount: Decimal = Field(ge=0)
    tax_rate: Decimal = Field(default=Decimal("0.00"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    matched_quantity: Decimal = Field(default=Decimal("0.00"), ge=0)


class InvoiceLineCreate(InvoiceLineBase):
    """Invoice Line creation schema."""

    pass


class InvoiceLineUpdate(BaseModel):
    """Invoice Line update schema."""

    product_code: Optional[str] = Field(default=None, max_length=100)
    product_description: Optional[str] = Field(default=None, max_length=500)
    quantity: Optional[Decimal] = Field(default=None, ge=0)
    unit_of_measure: Optional[str] = Field(default=None, max_length=20)
    unit_price: Optional[Decimal] = Field(default=None, ge=0)
    line_amount: Optional[Decimal] = Field(default=None, ge=0)
    tax_rate: Optional[Decimal] = Field(default=None, ge=0)
    tax_amount: Optional[Decimal] = Field(default=None, ge=0)
    matched_quantity: Optional[Decimal] = Field(default=None, ge=0)


class InvoiceLineResponse(InvoiceLineBase, UUIDMixin, TimestampMixin):
    """Invoice Line response schema."""

    model_config = ConfigDict(from_attributes=True)


class InvoiceBase(BaseModel):
    """Invoice base schema."""

    invoice_number: str = Field(max_length=100)
    supplier_id: str = Field(max_length=100)
    supplier_name: str = Field(max_length=255)
    supplier_reference: Optional[str] = Field(default=None, max_length=100)
    po_reference: Optional[str] = Field(default=None, max_length=50)
    status: str = Field(default="received")
    currency: str = Field(default="USD", max_length=3)
    subtotal: Decimal = Field(ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    total_amount: Decimal = Field(ge=0)
    invoice_date: date
    due_date: Optional[date] = None
    received_date: date
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    """Invoice creation schema."""

    lines: list[InvoiceLineCreate] = Field(default_factory=list)


class InvoiceUpdate(BaseModel):
    """Invoice update schema."""

    supplier_id: Optional[str] = Field(default=None, max_length=100)
    supplier_name: Optional[str] = Field(default=None, max_length=255)
    supplier_reference: Optional[str] = Field(default=None, max_length=100)
    po_reference: Optional[str] = Field(default=None, max_length=50)
    status: Optional[str] = None
    currency: Optional[str] = Field(default=None, max_length=3)
    subtotal: Optional[Decimal] = Field(default=None, ge=0)
    tax_amount: Optional[Decimal] = Field(default=None, ge=0)
    total_amount: Optional[Decimal] = Field(default=None, ge=0)
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    received_date: Optional[date] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class InvoiceResponse(InvoiceBase, UUIDMixin, TimestampMixin):
    """Invoice response schema."""

    model_config = ConfigDict(from_attributes=True)

    is_fully_matched: bool
    is_active: bool
    lines: list[InvoiceLineResponse] = Field(default_factory=list)


class InvoiceListResponse(BaseModel):
    """Invoice list response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    invoice_number: str
    supplier_id: str
    supplier_name: str
    status: str
    total_amount: Decimal
    invoice_date: date
    is_fully_matched: bool
    created_at: datetime

# api/schemas/invoice.py
"""Invoice schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class InvoiceLineBase(BaseModel):
    """Invoice Line base schema."""

    line_number: int = Field(ge=1)
    item_code: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=500)
    quantity: Decimal = Field(ge=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(ge=0)
    line_amount: Decimal = Field(ge=0)
    tax_rate: Decimal = Field(default=Decimal("0.0000"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    notes: Optional[str] = None


class InvoiceLineCreate(InvoiceLineBase):
    """Invoice Line creation schema."""

    pass


class InvoiceLineUpdate(BaseModel):
    """Invoice Line update schema."""

    line_number: Optional[int] = Field(default=None, ge=1)
    item_code: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, min_length=1, max_length=500)
    quantity: Optional[Decimal] = Field(default=None, ge=0)
    unit_of_measure: Optional[str] = Field(default=None, max_length=20)
    unit_price: Optional[Decimal] = Field(default=None, ge=0)
    line_amount: Optional[Decimal] = Field(default=None, ge=0)
    tax_rate: Optional[Decimal] = Field(default=None, ge=0)
    tax_amount: Optional[Decimal] = Field(default=None, ge=0)
    notes: Optional[str] = None


class InvoiceLineResponse(InvoiceLineBase):
    """Invoice Line response schema."""

    id: str
    invoice_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InvoiceBase(BaseModel):
    """Invoice base schema."""

    invoice_number: str = Field(min_length=1, max_length=50)
    supplier_id: str = Field(min_length=1, max_length=100)
    supplier_name: str = Field(min_length=1, max_length=255)
    invoice_date: date
    due_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    subtotal: Decimal = Field(default=Decimal("0.00"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    total_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    amount_paid: Decimal = Field(default=Decimal("0.00"), ge=0)
    status: str = Field(default="PENDING", max_length=20)
    notes: Optional[str] = None
    metadata_json: Optional[dict[str, Any]] = None


class InvoiceCreate(InvoiceBase):
    """Invoice creation schema."""

    lines: list[InvoiceLineCreate] = Field(default_factory=list)


class InvoiceUpdate(BaseModel):
    """Invoice update schema."""

    invoice_number: Optional[str] = Field(default=None, min_length=1, max_length=50)
    supplier_id: Optional[str] = Field(default=None, min_length=1, max_length=100)
    supplier_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    currency: Optional[str] = Field(default=None, max_length=3)
    subtotal: Optional[Decimal] = Field(default=None, ge=0)
    tax_amount: Optional[Decimal] = Field(default=None, ge=0)
    total_amount: Optional[Decimal] = Field(default=None, ge=0)
    amount_paid: Optional[Decimal] = Field(default=None, ge=0)
    status: Optional[str] = Field(default=None, max_length=20)
    notes: Optional[str] = None
    metadata_json: Optional[dict[str, Any]] = None


class InvoiceResponse(InvoiceBase):
    """Invoice response schema."""

    id: str
    lines: list[InvoiceLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InvoiceListResponse(BaseModel):
    """Invoice list response schema."""

    id: str
    invoice_number: str
    supplier_id: str
    supplier_name: str
    invoice_date: date
    total_amount: Decimal
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}

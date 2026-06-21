// src/app/schemas/invoice.py
"""Invoice schemas."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict


class InvoiceLineBase(BaseModel):
    """Base schema for Invoice line."""

    line_number: int
    product_code: Optional[str] = None
    product_description: str
    quantity: Decimal
    unit_of_measure: str = "EA"
    unit_price: Decimal
    metadata: Optional[dict] = None


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating an Invoice line."""

    pass


class InvoiceLineUpdate(BaseModel):
    """Schema for updating an Invoice line."""

    line_number: Optional[int] = None
    product_code: Optional[str] = None
    product_description: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit_of_measure: Optional[str] = None
    unit_price: Optional[Decimal] = None
    metadata: Optional[dict] = None


class InvoiceLineResponse(InvoiceLineBase):
    """Schema for Invoice line response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    invoice_id: uuid.UUID
    line_total: Decimal
    created_at: datetime
    updated_at: datetime


class InvoiceBase(BaseModel):
    """Base schema for Invoice."""

    invoice_number: str
    supplier_id: str
    supplier_name: str
    supplier_address: Optional[str] = None
    invoice_date: date
    due_date: Optional[date] = None
    po_reference: Optional[str] = None
    currency: str = "USD"
    notes: Optional[str] = None
    metadata: Optional[dict] = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating an Invoice."""

    lines: List[InvoiceLineCreate] = Field(default_factory=list)


class InvoiceUpdate(BaseModel):
    """Schema for updating an Invoice."""

    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    supplier_address: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[date] = None
    currency: Optional[str] = None
    notes: Optional[str] = None
    metadata: Optional[dict] = None


class InvoiceResponse(InvoiceBase):
    """Schema for Invoice response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    amount_paid: Decimal
    lines: List[InvoiceLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class InvoiceListResponse(BaseModel):
    """Schema for paginated Invoice list."""

    items: List[InvoiceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

// src/schemas/invoice.py
"""Invoice schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import Field, ConfigDict

from src.schemas.common import BaseSchema
from src.schemas.supplier import SupplierResponse
from src.models.enums import DocumentStatus


class InvoiceLineBase(BaseSchema):
    """Base invoice line schema."""
    line_number: int = Field(..., ge=1)
    product_code: Optional[str] = Field(None, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=0)
    tax_rate: Decimal = Field(default=Decimal("0.0000"), ge=0)


class InvoiceLineCreate(InvoiceLineBase):
    """Invoice line creation schema."""
    pass


class InvoiceLineUpdate(BaseSchema):
    """Invoice line update schema."""
    line_number: Optional[int] = Field(None, ge=1)
    product_code: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    tax_rate: Optional[Decimal] = Field(None, ge=0)


class InvoiceLineResponse(InvoiceLineBase):
    """Invoice line response schema."""
    id: UUID
    invoice_id: UUID
    line_total: Decimal
    tax_amount: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoiceBase(BaseSchema):
    """Base invoice schema."""
    invoice_number: str = Field(..., min_length=1, max_length=50)
    supplier_id: UUID
    po_reference: Optional[str] = Field(None, max_length=50)
    invoice_date: date
    due_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    payment_terms: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    attachment_url: Optional[str] = Field(None, max_length=500)


class InvoiceCreate(InvoiceBase):
    """Invoice creation schema."""
    lines: list[InvoiceLineCreate] = Field(default_factory=list)


class InvoiceUpdate(BaseSchema):
    """Invoice update schema."""
    invoice_number: Optional[str] = Field(None, min_length=1, max_length=50)
    supplier_id: Optional[UUID] = None
    po_reference: Optional[str] = Field(None, max_length=50)
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    status: Optional[DocumentStatus] = None
    currency: Optional[str] = Field(None, max_length=3)
    payment_terms: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    attachment_url: Optional[str] = Field(None, max_length=500)


class InvoiceResponse(InvoiceBase):
    """Invoice response schema."""
    id: UUID
    status: DocumentStatus
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    created_at: datetime
    updated_at: datetime
    lines: list[InvoiceLineResponse] = Field(default_factory=list)
    supplier: Optional[SupplierResponse] = None

    model_config = ConfigDict(from_attributes=True)

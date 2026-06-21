// src/schemas/invoice.py
"""Invoice schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.models.invoice import InvoiceStatus
from src.schemas.common import BaseSchema, TimestampSchema


class InvoiceLineBase(BaseSchema):
    """Base invoice line schema."""
    line_number: int
    sku: Optional[str] = None
    description: str = Field(max_length=500)
    quantity: Decimal = Field(gt=0)
    unit_of_measure: str = "EA"
    unit_price: Decimal = Field(ge=0)
    tax_rate: Decimal = Field(default=Decimal("0.00"), ge=0)


class InvoiceLineCreate(InvoiceLineBase):
    """Invoice line creation schema."""
    pass


class InvoiceLineResponse(InvoiceLineBase, TimestampSchema):
    """Invoice line response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    invoice_id: UUID
    line_total: Decimal


class InvoiceBase(BaseSchema):
    """Base invoice schema."""
    invoice_number: str = Field(max_length=50)
    supplier_id: str = Field(max_length=100)
    supplier_name: str = Field(max_length=255)
    supplier_reference: Optional[str] = None
    po_reference: Optional[str] = None
    invoice_date: str
    due_date: Optional[str] = None
    currency: str = "USD"
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    """Invoice creation schema."""
    lines: list[InvoiceLineCreate]


class InvoiceUpdate(BaseSchema):
    """Invoice update schema."""
    supplier_name: Optional[str] = None
    supplier_reference: Optional[str] = None
    due_date: Optional[str] = None
    status: Optional[InvoiceStatus] = None
    notes: Optional[str] = None
    lines: Optional[list[InvoiceLineCreate]] = None


class InvoiceResponse(InvoiceBase, TimestampSchema):
    """Invoice response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    status: InvoiceStatus
    lines: list[InvoiceLineResponse] = []

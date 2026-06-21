// src/schemas/invoice.py
"""Invoice schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from src.schemas.common import BaseSchema, TimestampMixin


class InvoiceLineBase(BaseSchema):
    """Base invoice line schema."""
    line_number: int
    item_code: str
    item_description: str
    quantity: Decimal
    unit_of_measure: str = "EA"
    unit_price: Decimal
    tax_code: Optional[str] = None
    tax_rate: Decimal = Decimal("0.00")


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating an invoice line."""
    po_line_id: Optional[UUID] = None


class InvoiceLineUpdate(BaseSchema):
    """Schema for updating an invoice line."""
    item_code: Optional[str] = None
    item_description: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit_of_measure: Optional[str] = None
    unit_price: Optional[Decimal] = None
    tax_code: Optional[str] = None
    tax_rate: Optional[Decimal] = None
    matched_quantity: Optional[Decimal] = None


class InvoiceLineResponse(InvoiceLineBase, TimestampMixin):
    """Schema for invoice line response."""
    id: UUID
    invoice_id: UUID
    line_amount: Decimal
    tax_amount: Decimal
    po_line_id: Optional[UUID] = None
    matched_quantity: Decimal

    model_config = ConfigDict(from_attributes=True)


class InvoiceBase(BaseSchema):
    """Base invoice schema."""
    invoice_number: str
    supplier_id: str
    supplier_name: str
    supplier_code: Optional[str] = None
    invoice_date: date
    due_date: Optional[date] = None
    invoice_type: str = "standard"
    po_reference: Optional[str] = None
    currency: str = "USD"
    payment_terms: Optional[str] = None
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating an invoice."""
    lines: list[InvoiceLineCreate]
    created_by_id: Optional[UUID] = None


class InvoiceUpdate(BaseSchema):
    """Schema for updating an invoice."""
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[str] = None
    po_reference: Optional[str] = None
    payment_terms: Optional[str] = None
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None


class InvoiceResponse(InvoiceBase, TimestampMixin):
    """Schema for invoice response."""
    id: UUID
    status: str
    received_date: date
    po_id: Optional[UUID] = None
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    payment_reference: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_by_id: Optional[UUID] = None
    approved_by_id: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    lines: list[InvoiceLineResponse] = []

    model_config = ConfigDict(from_attributes=True)


class InvoiceSummary(BaseSchema):
    """Summary of invoice for lists."""
    id: UUID
    invoice_number: str
    supplier_name: str
    invoice_date: date
    status: str
    total_amount: Decimal
    po_reference: Optional[str] = None
    match_status: str = "unmatched"

    model_config = ConfigDict(from_attributes=True)

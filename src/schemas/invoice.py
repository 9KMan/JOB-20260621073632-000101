// src/schemas/invoice.py
"""Invoice schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.base import BaseSchema


class InvoiceLineBase(BaseSchema):
    """Base invoice line schema."""
    line_number: int
    item_code: Optional[str] = None
    item_description: str
    quantity: Decimal
    unit_of_measure: str = "EA"
    unit_price: Decimal
    tax_rate: Decimal = Decimal("0.00")
    tax_amount: Decimal = Decimal("0.00")
    line_total: Decimal
    po_line_id: Optional[str] = None
    dn_line_id: Optional[str] = None
    match_score: Optional[Decimal] = None


class InvoiceLineCreate(InvoiceLineBase):
    """Invoice line creation schema."""
    pass


class InvoiceLineUpdate(BaseSchema):
    """Invoice line update schema."""
    item_code: Optional[str] = None
    item_description: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit_of_measure: Optional[str] = None
    unit_price: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    po_line_id: Optional[str] = None
    dn_line_id: Optional[str] = None


class InvoiceLineResponse(InvoiceLineBase):
    """Invoice line response schema."""
    id: str
    invoice_id: str
    created_at: datetime
    updated_at: datetime


class InvoiceBase(BaseSchema):
    """Base invoice schema."""
    invoice_number: str
    supplier_id: str
    supplier_name: str
    supplier_code: Optional[str] = None
    po_id: Optional[str] = None
    po_number: Optional[str] = None
    invoice_date: date
    due_date: Optional[date] = None
    receipt_date: Optional[datetime] = None
    status: str = "pending"
    currency: str = "USD"
    notes: Optional[str] = None
    payment_terms: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    """Invoice creation schema."""
    subtotal: Decimal = Decimal("0.00")
    tax_amount: Decimal = Decimal("0.00")
    total_amount: Decimal
    lines: List[InvoiceLineCreate] = Field(default_factory=list)


class InvoiceUpdate(BaseSchema):
    """Invoice update schema."""
    supplier_name: Optional[str] = None
    supplier_code: Optional[str] = None
    po_id: Optional[str] = None
    po_number: Optional[str] = None
    due_date: Optional[date] = None
    receipt_date: Optional[datetime] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    payment_terms: Optional[str] = None
    payment_reference: Optional[str] = None
    matched_by: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None


class InvoiceResponse(InvoiceBase):
    """Invoice response schema."""
    id: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    amount_paid: Decimal
    match_score: Optional[Decimal] = None
    match_status: Optional[str] = None
    received_by: Optional[str] = None
    matched_by: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    lines: List[InvoiceLineResponse] = Field(default_factory=list)

// src/app/schemas/invoice.py
"""
Invoice schemas for API request/response validation.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.base import BaseSchema, TimestampSchema, PaginationParams, PaginatedResponse
from app.schemas.supplier import SupplierBrief
from app.schemas.purchase_order import PurchaseOrderBrief


# Line item schemas
class InvoiceLineCreate(BaseSchema):
    """Schema for creating an invoice line."""
    line_number: int = Field(..., ge=1)
    description: str = Field(..., min_length=1, max_length=500)
    sku: Optional[str] = Field(None, max_length=100)
    quantity: Decimal = Field(..., gt=0)
    unit_of_measure: str = Field(default="EA")
    unit_price: Decimal = Field(..., ge=0)
    tax_rate: Decimal = Field(default=Decimal("0.0000"), ge=0)
    po_line_id: Optional[UUID] = None
    delivery_note_line_id: Optional[UUID] = None


class InvoiceLineUpdate(BaseSchema):
    """Schema for updating an invoice line."""
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    sku: Optional[str] = Field(None, max_length=100)
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit_of_measure: Optional[str] = None
    unit_price: Optional[Decimal] = Field(None, ge=0)
    tax_rate: Optional[Decimal] = Field(None, ge=0)


class InvoiceLineResponse(BaseSchema):
    """Invoice line response schema."""
    id: UUID
    line_number: int
    description: str
    sku: Optional[str]
    quantity: Decimal
    unit_of_measure: str
    unit_price: Decimal
    tax_rate: Decimal
    line_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    po_line_id: Optional[UUID]
    delivery_note_line_id: Optional[UUID]


# Header schemas
class InvoiceCreate(BaseSchema):
    """Schema for creating an invoice."""
    invoice_number: str = Field(..., min_length=1, max_length=50)
    supplier_id: UUID
    po_id: Optional[UUID] = None
    invoice_date: date
    due_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None
    lines: List[InvoiceLineCreate]


class InvoiceUpdate(BaseSchema):
    """Schema for updating an invoice."""
    po_id: Optional[UUID] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    payment_reference: Optional[str] = None


class InvoiceResponse(TimestampSchema):
    """Invoice response schema."""
    id: UUID
    invoice_number: str
    supplier_id: UUID
    po_id: Optional[UUID]
    invoice_date: date
    due_date: Optional[date]
    status: str
    currency: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    amount_paid: Decimal
    notes: Optional[str]
    payment_reference: Optional[str]
    lines: List[InvoiceLineResponse] = []
    supplier: Optional[SupplierBrief] = None
    purchase_order: Optional[PurchaseOrderBrief] = None


class InvoiceBrief(BaseSchema):
    """Brief invoice information."""
    id: UUID
    invoice_number: str
    total_amount: Decimal
    status: str


class InvoiceListResponse(PaginatedResponse[InvoiceResponse]):
    """Paginated invoice list response."""
    pass


class InvoiceStatusUpdate(BaseSchema):
    """Schema for updating invoice status."""
    status: str = Field(..., description="New status: pending, matched, approved, paid, disputed")


class InvoicePaymentUpdate(BaseSchema):
    """Schema for recording payment."""
    amount: Decimal = Field(..., gt=0)
    payment_reference: str

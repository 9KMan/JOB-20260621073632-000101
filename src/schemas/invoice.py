// src/schemas/invoice.py
"""Invoice schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from src.schemas.common import BaseSchema, UUIDMixin


class InvoiceLineBase(BaseModel):
    """Base schema for invoice line items."""
    line_number: int
    sku: Optional[str] = None
    description: str
    quantity: Decimal
    unit_price: Decimal
    tax_amount: Decimal = Decimal("0")
    total_amount: Decimal
    uom: str = "EA"
    po_line_id: Optional[UUID] = None
    metadata: Optional[dict] = None


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating invoice line items."""
    pass


class InvoiceLineUpdate(BaseModel):
    """Schema for updating invoice line items."""
    sku: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit_price: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    uom: Optional[str] = None
    po_line_id: Optional[UUID] = None
    metadata: Optional[dict] = None


class InvoiceLineResponse(UUIDMixin, BaseSchema):
    """Response schema for invoice line items."""
    invoice_id: UUID
    line_number: int
    sku: Optional[str]
    description: str
    quantity: Decimal
    unit_price: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    uom: str
    po_line_id: Optional[UUID]
    metadata: Optional[dict]
    created_at: datetime
    updated_at: datetime


class InvoiceBase(BaseModel):
    """Base schema for invoices."""
    invoice_number: str = Field(max_length=50)
    supplier_id: str = Field(max_length=100)
    supplier_name: str = Field(max_length=255)
    supplier_reference: Optional[str] = None
    invoice_date: date
    due_date: Optional[date] = None
    subtotal: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    total_amount: Decimal = Decimal("0")
    currency: str = Field(default="USD", max_length=3)
    status: str = "RECEIVED"
    payment_status: str = "UNPAID"
    notes: Optional[str] = None
    metadata: Optional[dict] = None
    purchase_order_id: Optional[UUID] = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating an invoice."""
    lines: list[InvoiceLineCreate] = Field(default_factory=list)


class InvoiceUpdate(BaseModel):
    """Schema for updating an invoice."""
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    supplier_reference: Optional[str] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    subtotal: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    currency: Optional[str] = None
    status: Optional[str] = None
    payment_status: Optional[str] = None
    notes: Optional[str] = None
    metadata: Optional[dict] = None
    purchase_order_id: Optional[UUID] = None


class InvoiceResponse(UUIDMixin, BaseSchema):
    """Response schema for invoices."""
    invoice_number: str
    supplier_id: str
    supplier_name: str
    supplier_reference: Optional[str]
    invoice_date: date
    due_date: Optional[date]
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    currency: str
    status: str
    payment_status: str
    notes: Optional[str]
    metadata: Optional[dict]
    purchase_order_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    is_deleted: bool


class InvoiceListResponse(BaseSchema):
    """Response schema for listing invoices."""
    id: UUID
    invoice_number: str
    supplier_id: str
    supplier_name: str
    invoice_date: date
    total_amount: Decimal
    currency: str
    status: str
    payment_status: str
    created_at: datetime

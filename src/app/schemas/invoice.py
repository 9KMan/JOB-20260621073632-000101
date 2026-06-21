# src/app/schemas/invoice.py
"""Invoice schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.app.schemas.common import BaseSchema, TimestampMixin, UUIDMixin
from src.app.models.enums import DocumentStatus, LineStatus


class InvoiceLineBase(BaseSchema):
    """Base invoice line schema."""
    line_number: int = Field(..., ge=1)
    description: str = Field(..., min_length=1, max_length=500)
    sku: Optional[str] = Field(None, max_length=100)
    quantity_invoiced: Decimal = Field(..., ge=0)
    unit_price: Decimal = Field(..., ge=0)
    line_amount: Decimal = Field(..., ge=0)
    status: LineStatus = Field(default=LineStatus.PENDING)


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating an invoice line."""
    pass


class InvoiceLineUpdate(BaseSchema):
    """Schema for updating an invoice line."""
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    sku: Optional[str] = Field(None, max_length=100)
    quantity_invoiced: Optional[Decimal] = Field(None, ge=0)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    line_amount: Optional[Decimal] = Field(None, ge=0)
    status: Optional[LineStatus] = None


class InvoiceLineRead(UUIDMixin, TimestampMixin, InvoiceLineBase):
    """Schema for reading an invoice line."""
    invoice_id: UUID
    deleted_at: Optional[datetime] = None
    is_deleted: bool = False


class InvoiceBase(BaseSchema):
    """Base invoice schema."""
    supplier_id: str = Field(..., min_length=1, max_length=100)
    supplier_name: str = Field(..., min_length=1, max_length=255)
    invoice_number: str = Field(..., min_length=1, max_length=100)
    invoice_date: date
    due_date: Optional[date] = None
    currency: str = Field(default="USD", min_length=3, max_length=3)
    total_amount: Decimal = Field(..., ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    status: DocumentStatus = Field(default=DocumentStatus.RECEIVED)
    notes: Optional[str] = None
    metadata: Optional[dict] = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating an invoice."""
    lines: list[InvoiceLineCreate] = Field(default_factory=list)


class InvoiceUpdate(BaseSchema):
    """Schema for updating an invoice."""
    supplier_id: Optional[str] = Field(None, min_length=1, max_length=100)
    supplier_name: Optional[str] = Field(None, min_length=1, max_length=255)
    invoice_number: Optional[str] = Field(None, min_length=1, max_length=100)
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    total_amount: Optional[Decimal] = Field(None, ge=0)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    status: Optional[DocumentStatus] = None
    notes: Optional[str] = None
    metadata: Optional[dict] = None


class InvoiceRead(UUIDMixin, TimestampMixin, InvoiceBase):
    """Schema for reading an invoice."""
    deleted_at: Optional[datetime] = None
    is_deleted: bool = False
    lines: list[InvoiceLineRead] = Field(default_factory=list)

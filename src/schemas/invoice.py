// src/schemas/invoice.py
"""Invoice schemas."""
from typing import Optional, List
from datetime import date
from decimal import Decimal
from uuid import UUID
from pydantic import Field, ConfigDict

from src.schemas.base import BaseSchema, TimestampUUIDSchema
from src.models.enums import DocumentStatus


class InvoiceLineBase(BaseSchema):
    """Base invoice line schema."""
    
    line_number: int = Field(..., ge=1)
    product_code: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., min_length=1, max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=0)
    line_amount: Decimal = Field(..., ge=0)


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating an invoice line."""
    pass


class InvoiceLineResponse(TimestampUUIDSchema):
    """Schema for invoice line response."""
    
    invoice_id: UUID
    line_number: int
    product_code: str
    description: str
    quantity: Decimal
    unit_of_measure: str
    unit_price: Decimal
    line_amount: Decimal


class InvoiceBase(BaseSchema):
    """Base invoice schema."""
    
    invoice_number: str = Field(..., min_length=1, max_length=50)
    supplier_id: UUID
    po_id: Optional[UUID] = None
    invoice_date: date
    due_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = Field(None, max_length=1000)


class InvoiceCreate(InvoiceBase):
    """Schema for creating an invoice."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    lines: List[InvoiceLineCreate] = Field(..., min_length=1)
    subtotal: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None


class InvoiceUpdate(BaseSchema):
    """Schema for updating an invoice."""
    
    invoice_number: Optional[str] = Field(None, min_length=1, max_length=50)
    supplier_id: Optional[UUID] = None
    po_id: Optional[UUID] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    status: Optional[DocumentStatus] = None
    currency: Optional[str] = Field(None, max_length=3)
    notes: Optional[str] = Field(None, max_length=1000)


class InvoiceResponse(TimestampUUIDSchema):
    """Schema for invoice response."""
    
    invoice_number: str
    supplier_id: UUID
    po_id: Optional[UUID] = None
    invoice_date: date
    due_date: Optional[date] = None
    status: DocumentStatus
    currency: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    notes: Optional[str] = None
    lines: List[InvoiceLineResponse] = []


class InvoiceListResponse(BaseSchema):
    """Schema for invoice list response without lines."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    invoice_number: str
    supplier_id: UUID
    po_id: Optional[UUID] = None
    invoice_date: date
    due_date: Optional[date] = None
    status: DocumentStatus
    currency: str
    total_amount: Decimal
    created_at: date
    updated_at: date

// src/schemas/invoice.py
"""
FinaRo AP Automation Core Engine
Invoice Pydantic Schemas
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.base import BaseSchema


class InvoiceLineBase(BaseSchema):
    """Base schema for Invoice Line."""
    line_number: int = Field(..., ge=1)
    internal_reference: Optional[str] = None
    product_id: Optional[UUID] = None
    product_code: Optional[str] = None
    product_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    quantity_invoiced: Decimal = Field(..., ge=Decimal('0'))
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=Decimal('0'))
    tax_rate: Decimal = Field(default=Decimal('0'), ge=Decimal('0'))


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating an Invoice Line."""
    pass


class InvoiceLineUpdate(BaseSchema):
    """Schema for updating an Invoice Line."""
    line_number: Optional[int] = Field(None, ge=1)
    internal_reference: Optional[str] = None
    product_id: Optional[UUID] = None
    product_code: Optional[str] = None
    product_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    quantity_invoiced: Optional[Decimal] = Field(None, ge=Decimal('0'))
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    unit_price: Optional[Decimal] = Field(None, ge=Decimal('0'))
    tax_rate: Optional[Decimal] = Field(None, ge=Decimal('0'))
    quantity_matched: Optional[Decimal] = Field(None, ge=Decimal('0'))
    status: Optional[str] = None


class InvoiceLineResponse(InvoiceLineBase):
    """Schema for Invoice Line response."""
    id: UUID
    invoice_id: UUID
    line_total: Decimal
    tax_amount: Decimal
    quantity_matched: Decimal
    quantity_unmatched: Decimal
    status: str
    created_at: datetime
    updated_at: datetime


class InvoiceBase(BaseSchema):
    """Base schema for Invoice."""
    invoice_number: str = Field(..., min_length=1, max_length=50)
    supplier_id: UUID
    supplier_name: str = Field(..., min_length=1, max_length=255)
    supplier_code: Optional[str] = None
    po_id: Optional[UUID] = None
    supplier_invoice_number: Optional[str] = None
    invoice_date: date
    due_date: Optional[date] = None
    received_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    subtotal: Decimal = Field(default=Decimal('0'))
    tax_amount: Decimal = Field(default=Decimal('0'))
    total_amount: Decimal = Field(default=Decimal('0'))
    tax_id: Optional[str] = None
    tax_rate: Decimal = Field(default=Decimal('0'), ge=Decimal('0'))
    payment_terms: Optional[str] = None
    payment_method: Optional[str] = None
    notes: Optional[str] = None
    department: Optional[str] = None
    raw_ocr_data: Optional[str] = None
    confidence_score: Optional[Decimal] = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating an Invoice."""
    lines: List[InvoiceLineCreate] = Field(default_factory=list)


class InvoiceUpdate(BaseSchema):
    """Schema for updating an Invoice."""
    invoice_number: Optional[str] = Field(None, min_length=1, max_length=50)
    supplier_id: Optional[UUID] = None
    supplier_name: Optional[str] = Field(None, min_length=1, max_length=255)
    supplier_code: Optional[str] = None
    po_id: Optional[UUID] = None
    supplier_invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    currency: Optional[str] = Field(None, max_length=3)
    subtotal: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    tax_id: Optional[str] = None
    tax_rate: Optional[Decimal] = Field(None, ge=Decimal('0'))
    payment_terms: Optional[str] = None
    payment_method: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    department: Optional[str] = None
    amount_paid: Optional[Decimal] = Field(None, ge=Decimal('0'))
    rejection_reason: Optional[str] = None


class InvoiceResponse(InvoiceBase):
    """Schema for Invoice response."""
    id: UUID
    status: str
    amount_paid: Decimal
    balance_due: Decimal
    is_paid: bool
    lines: List[InvoiceLineResponse]
    created_at: datetime
    updated_at: datetime
    
    @field_validator('lines', mode='before')
    @classmethod
    def validate_lines(cls, v):
        if v is None:
            return []
        return v


class InvoiceListResponse(BaseSchema):
    """Schema for Invoice list item response."""
    id: UUID
    invoice_number: str
    supplier_id: UUID
    supplier_name: str
    invoice_date: date
    due_date: Optional[date]
    status: str
    total_amount: Decimal
    balance_due: Decimal
    currency: str
    department: Optional[str]
    created_at: datetime

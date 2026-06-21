// src/api/schemas/invoice.py
from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from src.models.invoice import InvoiceStatus


class InvoiceLineBase(BaseModel):
    """Base invoice line schema."""
    line_number: int
    item_code: Optional[str] = None
    description: str = Field(..., max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_of_measure: str = "EA"
    unit_price: Decimal = Field(..., ge=0)
    tax_rate: Decimal = Field(default=Decimal("0"), ge=0, le=1)


class InvoiceLineCreate(InvoiceLineBase):
    """Invoice line creation schema."""
    matched_po_line_id: Optional[UUID] = None


class InvoiceLineResponse(InvoiceLineBase):
    """Invoice line response schema."""
    id: UUID
    line_total: Decimal
    tax_amount: Decimal
    matched_po_line_id: Optional[UUID] = None
    matched_dn_line_id: Optional[UUID] = None
    
    class Config:
        from_attributes = True


class InvoiceBase(BaseModel):
    """Base invoice schema."""
    invoice_number: str = Field(..., max_length=100)
    supplier_id: UUID
    supplier_name: str = Field(..., max_length=255)
    supplier_code: Optional[str] = None
    invoice_date: date
    due_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None
    payment_terms: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    """Invoice creation schema."""
    line_items: List[InvoiceLineCreate] = Field(default_factory=list)


class InvoiceUpdate(BaseModel):
    """Invoice update schema."""
    supplier_name: Optional[str] = None
    supplier_code: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[InvoiceStatus] = None
    notes: Optional[str] = None
    payment_terms: Optional[str] = None


class InvoiceResponse(InvoiceBase):
    """Invoice response schema."""
    id: UUID
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    status: InvoiceStatus
    matched_po_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    line_items: List[InvoiceLineResponse] = []
    
    class Config:
        from_attributes = True


class InvoiceListResponse(BaseModel):
    """Invoice list response schema."""
    items: List[InvoiceResponse]
    total: int
    page: int
    page_size: int

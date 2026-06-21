// src/api/schemas/invoice.py
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from datetime import date
from src.models.invoice import InvoiceStatus


class InvoiceLineBase(BaseModel):
    line_number: int
    product_code: Optional[str] = None
    description: str
    quantity: Decimal
    unit_of_measure: str = "EA"
    unit_price: Decimal


class InvoiceLineCreate(InvoiceLineBase):
    pass


class InvoiceLineResponse(InvoiceLineBase):
    id: UUID
    line_total: Decimal
    
    class Config:
        from_attributes = True


class InvoiceBase(BaseModel):
    invoice_number: str
    supplier_code: str
    supplier_name: str
    invoice_date: date
    due_date: Optional[date] = None
    purchase_order_id: Optional[UUID] = None
    currency: str = "USD"
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    lines: List[InvoiceLineCreate]


class InvoiceUpdate(BaseModel):
    supplier_code: Optional[str] = None
    supplier_name: Optional[str] = None
    status: Optional[InvoiceStatus] = None
    due_date: Optional[date] = None
    notes: Optional[str] = None


class InvoiceResponse(InvoiceBase):
    id: UUID
    status: InvoiceStatus
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    created_at: date
    updated_at: date
    lines: List[InvoiceLineResponse] = []
    
    class Config:
        from_attributes = True

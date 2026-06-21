// src/schemas/invoice.py
"""Invoice schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.document import DocumentLineCreate, DocumentLineResponse


class InvoiceBase(BaseModel):
    """Base invoice schema."""
    document_number: str = Field(..., max_length=100)
    supplier_code: str = Field(..., max_length=100)
    supplier_name: str = Field(..., max_length=255)
    supplier_tax_id: Optional[str] = Field(None, max_length=50)
    reference_number: Optional[str] = Field(None, max_length=100)
    po_reference: Optional[str] = Field(None, max_length=100)
    document_date: date
    due_date: Optional[date] = None
    payment_method: Optional[str] = Field(None, max_length=50)
    bank_details: Optional[str] = None
    tax_id: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None
    currency: str = Field(default="USD", max_length=3)


class InvoiceCreate(InvoiceBase):
    """Invoice creation schema."""
    lines: list[DocumentLineCreate] = Field(..., min_length=1)


class InvoiceUpdate(BaseModel):
    """Invoice update schema."""
    supplier_code: Optional[str] = Field(None, max_length=100)
    supplier_name: Optional[str] = Field(None, max_length=255)
    supplier_tax_id: Optional[str] = Field(None, max_length=50)
    due_date: Optional[date] = None
    payment_method: Optional[str] = Field(None, max_length=50)
    bank_details: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class InvoiceResponse(InvoiceBase):
    """Invoice response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    discount_percent: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    open_amount: Decimal
    lines: list[DocumentLineResponse] = []
    created_at: datetime
    updated_at: datetime

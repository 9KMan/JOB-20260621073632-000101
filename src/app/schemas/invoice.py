// src/app/schemas/invoice.py
"""Invoice schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class InvoiceLineBase(BaseModel):
    """Base invoice line schema."""
    
    line_number: int = Field(ge=1)
    product_code: Optional[str] = Field(default=None, max_length=100)
    product_name: str = Field(max_length=255)
    description: Optional[str] = None
    quantity: Decimal = Field(ge=0, decimal_places=3)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(ge=0, decimal_places=4)
    tax_code: Optional[str] = None
    tax_rate: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    notes: Optional[str] = None


class InvoiceLineCreate(InvoiceLineBase):
    """Invoice line creation schema."""
    pass


class InvoiceLineResponse(InvoiceLineBase):
    """Invoice line response schema."""
    
    id: str
    invoice_id: str
    line_amount: Decimal
    po_line_id: Optional[str] = None
    dn_line_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class InvoiceBase(BaseModel):
    """Base invoice schema."""
    
    invoice_number: str = Field(max_length=50)
    supplier_id: str
    supplier_name: str = Field(max_length=255)
    supplier_code: str = Field(max_length=50)
    invoice_date: date
    due_date: date
    po_reference: Optional[str] = None
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    """Invoice creation schema."""
    
    lines: list[InvoiceLineCreate] = Field(min_length=1)
    status: Optional[str] = "draft"


class InvoiceUpdate(BaseModel):
    """Invoice update schema."""
    
    supplier_name: Optional[str] = None
    supplier_code: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class InvoiceResponse(InvoiceBase):
    """Invoice response schema."""
    
    id: str
    po_id: Optional[str] = None
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    status: str
    is_archived: bool
    lines: list[InvoiceLineResponse] = []
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class InvoiceListResponse(BaseModel):
    """Invoice list response with pagination."""
    
    invoices: list[InvoiceResponse]
    total: int
    page: int
    page_size: int


class InvoiceSummary(BaseModel):
    """Invoice summary for matching."""
    
    id: str
    invoice_number: str
    supplier_code: str
    total_amount: Decimal
    currency: str
    status: str
    open_amount: Decimal
    line_count: int
    
    model_config = ConfigDict(from_attributes=True)

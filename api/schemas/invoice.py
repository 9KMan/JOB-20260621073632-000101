// api/schemas/invoice.py
"""Invoice Pydantic schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# Line schemas
class InvoiceLineBase(BaseModel):
    """Base schema for Invoice line items."""
    
    line_number: int = Field(ge=1)
    item_code: Optional[str] = Field(None, max_length=50)
    item_description: str = Field(max_length=500)
    quantity: Decimal = Field(ge=0)
    unit_price: Decimal = Field(ge=0)
    tax_rate: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating an Invoice line item."""
    
    matched_po_line_id: Optional[UUID] = None
    matched_dn_line_id: Optional[UUID] = None


class InvoiceLineUpdate(BaseModel):
    """Schema for updating an Invoice line item."""
    
    item_code: Optional[str] = Field(None, max_length=50)
    item_description: Optional[str] = Field(None, max_length=500)
    quantity: Optional[Decimal] = Field(None, ge=0)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    matched_po_line_id: Optional[UUID] = None
    matched_dn_line_id: Optional[UUID] = None
    match_confidence: Optional[Decimal] = Field(None, ge=0, le=1)
    notes: Optional[str] = None


class InvoiceLineResponse(InvoiceLineBase):
    """Schema for Invoice line item response."""
    
    id: UUID
    invoice_id: UUID
    line_total: Decimal
    tax_amount: Decimal
    matched_po_line_id: Optional[UUID] = None
    matched_dn_line_id: Optional[UUID] = None
    match_confidence: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


# Invoice schemas
class InvoiceBase(BaseModel):
    """Base schema for Invoices."""
    
    invoice_number: str = Field(max_length=50)
    supplier_id: UUID
    supplier_name: str = Field(max_length=255)
    supplier_code: Optional[str] = Field(None, max_length=50)
    po_reference: Optional[str] = Field(None, max_length=50)
    invoice_date: date
    due_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None
    metadata: Optional[dict] = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating an Invoice."""
    
    lines: List[InvoiceLineCreate] = Field(default_factory=list)
    
    @field_validator("invoice_number")
    @classmethod
    def validate_invoice_number(cls, v: str) -> str:
        return v.strip().upper()


class InvoiceUpdate(BaseModel):
    """Schema for updating an Invoice."""
    
    supplier_name: Optional[str] = Field(None, max_length=255)
    supplier_code: Optional[str] = Field(None, max_length=50)
    due_date: Optional[date] = None
    status: Optional[str] = None
    amount_paid: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None
    metadata: Optional[dict] = None
    is_matched: Optional[bool] = None


class InvoiceResponse(InvoiceBase):
    """Schema for Invoice response."""
    
    id: UUID
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    amount_paid: Decimal
    balance_due: Decimal
    status: str
    is_matched: bool
    matched_at: Optional[datetime] = None
    line_count: int
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class InvoiceDetailResponse(InvoiceResponse):
    """Schema for detailed Invoice response with lines."""
    
    lines: List[InvoiceLineResponse] = []
    
    model_config = {"from_attributes": True}


class InvoiceListResponse(BaseModel):
    """Schema for paginated list of Invoices."""
    
    items: List[InvoiceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

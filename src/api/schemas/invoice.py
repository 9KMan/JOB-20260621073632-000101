// src/api/schemas/invoice.py
"""Invoice schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class InvoiceLineBase(BaseModel):
    """Base invoice line schema."""
    line_number: int = Field(ge=1)
    item_code: Optional[str] = Field(default=None, max_length=50)
    description: str = Field(min_length=1, max_length=500)
    quantity: Decimal = Field(gt=0, decimal_places=3)
    unit_of_measure: Optional[str] = Field(default=None, max_length=20)
    unit_price: Decimal = Field(ge=0, decimal_places=2)
    tax_rate: Optional[Decimal] = Field(default=None, ge=0, le=100)


class InvoiceLineCreate(InvoiceLineBase):
    """Invoice line creation schema."""
    line_amount: Optional[Decimal] = Field(default=None, ge=0)
    
    def calculate_amounts(self) -> tuple[Decimal, Decimal]:
        """Calculate line amount and tax amount."""
        line_amount = self.quantity * self.unit_price
        tax_amount = Decimal("0")
        if self.tax_rate:
            tax_amount = line_amount * (self.tax_rate / 100)
        return line_amount, tax_amount


class InvoiceLineUpdate(BaseModel):
    """Invoice line update schema."""
    item_code: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit_of_measure: Optional[str] = None
    unit_price: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None


class InvoiceLineResponse(InvoiceLineBase):
    """Invoice line response schema."""
    id: UUID
    invoice_id: UUID
    line_amount: Decimal
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class InvoiceBase(BaseModel):
    """Base invoice schema."""
    invoice_number: str = Field(min_length=1, max_length=50)
    supplier_id: UUID
    po_id: Optional[UUID] = None
    invoice_date: date
    due_date: Optional[date] = None
    currency: str = Field(default="USD", min_length=3, max_length=3)
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    """Invoice creation schema."""
    lines: List[InvoiceLineCreate] = Field(min_length=1)
    tax_amount: Optional[Decimal] = None
    
    def calculate_totals(self) -> tuple[Decimal, Decimal]:
        """Calculate total amount and tax amount."""
        total = Decimal("0")
        tax_total = Decimal("0")
        for line in self.lines:
            line_amount = line.quantity * line.unit_price
            total += line_amount
            if line.tax_rate:
                tax_total += line_amount * (line.tax_rate / 100)
        return total, tax_total


class InvoiceUpdate(BaseModel):
    """Invoice update schema."""
    supplier_id: Optional[UUID] = None
    po_id: Optional[UUID] = None
    status: Optional[str] = None
    due_date: Optional[date] = None
    notes: Optional[str] = None


class InvoiceResponse(InvoiceBase):
    """Invoice response schema."""
    id: UUID
    status: str
    total_amount: Decimal
    tax_amount: Optional[Decimal] = None
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    lines: List[InvoiceLineResponse] = []
    
    model_config = {"from_attributes": True}


class InvoiceListResponse(BaseModel):
    """Invoice list response schema."""
    items: List[InvoiceResponse]
    total: int
    page: int
    size: int
    pages: int

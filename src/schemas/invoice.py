// src/schemas/invoice.py
"""Invoice schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class InvoiceLineBase(BaseModel):
    """Base invoice line schema."""
    
    line_number: int = Field(..., ge=1)
    item_code: Optional[str] = Field(None, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=0)
    tax_rate: Decimal = Field(default=Decimal("0.0000"), ge=0)
    line_total: Decimal = Field(..., ge=0)


class InvoiceLineCreate(InvoiceLineBase):
    """Invoice line creation schema."""
    pass


class InvoiceLineUpdate(BaseModel):
    """Invoice line update schema."""
    
    item_code: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    tax_rate: Optional[Decimal] = Field(None, ge=0)
    line_total: Optional[Decimal] = Field(None, ge=0)


class InvoiceLineResponse(BaseModel):
    """Invoice line response schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    line_number: int
    item_code: Optional[str] = None
    description: str
    quantity: Decimal
    unit_of_measure: str
    unit_price: Decimal
    tax_rate: Decimal
    line_total: Decimal
    created_at: datetime
    updated_at: datetime


class InvoiceBase(BaseModel):
    """Base invoice schema."""
    
    invoice_number: str = Field(..., min_length=1, max_length=100)
    vendor_id: UUID
    po_reference: Optional[str] = Field(None, max_length=50)
    invoice_date: date
    due_date: date
    status: str = Field(default="pending", max_length=50)
    currency: str = Field(default="USD", max_length=3)
    subtotal: Decimal = Field(default=Decimal("0.00"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    total_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    amount_paid: Decimal = Field(default=Decimal("0.00"), ge=0)
    notes: Optional[str] = None
    attachments: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    """Invoice creation schema."""
    
    lines: List[InvoiceLineCreate] = Field(default_factory=list)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "invoice_number": "INV-2024-001",
                "vendor_id": "uuid-here",
                "po_reference": "PO-2024-001",
                "invoice_date": "2024-01-20",
                "due_date": "2024-02-19",
                "status": "pending",
                "currency": "USD",
                "subtotal": Decimal("1000.00"),
                "tax_amount": Decimal("100.00"),
                "total_amount": Decimal("1100.00"),
                "amount_paid": Decimal("0.00"),
                "lines": []
            }
        }
    )


class InvoiceUpdate(BaseModel):
    """Invoice update schema."""
    
    invoice_number: Optional[str] = Field(None, min_length=1, max_length=100)
    vendor_id: Optional[UUID] = None
    po_reference: Optional[str] = Field(None, max_length=50)
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    status: Optional[str] = Field(None, max_length=50)
    currency: Optional[str] = Field(None, max_length=3)
    subtotal: Optional[Decimal] = Field(None, ge=0)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    total_amount: Optional[Decimal] = Field(None, ge=0)
    amount_paid: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None
    attachments: Optional[str] = None


class InvoiceResponse(BaseModel):
    """Invoice response schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    invoice_number: str
    vendor_id: UUID
    po_reference: Optional[str] = None
    invoice_date: date
    due_date: date
    status: str
    currency: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    amount_paid: Decimal
    notes: Optional[str] = None
    attachments: Optional[str] = None
    received_at: datetime
    created_at: datetime
    updated_at: datetime
    lines: List[InvoiceLineResponse] = Field(default_factory=list)

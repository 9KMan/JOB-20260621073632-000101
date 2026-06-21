# src/app/schemas/invoice.py
"""Invoice schemas."""
import uuid
import decimal
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict

from src.app.schemas.base import BaseSchema
from src.app.schemas.supplier import SupplierResponse


class InvoiceLineBase(BaseSchema):
    """Base invoice line schema."""
    
    line_number: int = Field(..., ge=1)
    purchase_order_line_id: Optional[uuid.UUID] = None
    delivery_note_line_id: Optional[uuid.UUID] = None
    item_code: Optional[str] = Field(None, max_length=50)
    item_description: str = Field(..., min_length=1, max_length=500)
    quantity: decimal.Decimal = Field(..., gt=0)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    unit_price: decimal.Decimal = Field(..., ge=0)
    tax_rate: decimal.Decimal = Field(default=decimal.Decimal("0.0000"), ge=0)


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating an invoice line."""
    
    pass


class InvoiceLineUpdate(BaseSchema):
    """Schema for updating an invoice line."""
    
    purchase_order_line_id: Optional[uuid.UUID] = None
    delivery_note_line_id: Optional[uuid.UUID] = None
    item_code: Optional[str] = Field(None, max_length=50)
    item_description: Optional[str] = Field(None, min_length=1, max_length=500)
    quantity: Optional[decimal.Decimal] = Field(None, gt=0)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    unit_price: Optional[decimal.Decimal] = Field(None, ge=0)
    tax_rate: Optional[decimal.Decimal] = Field(None, ge=0)


class InvoiceLineResponse(InvoiceLineBase):
    """Schema for invoice line response."""
    
    id: uuid.UUID
    invoice_id: uuid.UUID
    line_total: decimal.Decimal
    tax_amount: decimal.Decimal
    created_at: datetime
    updated_at: datetime


class InvoiceBase(BaseSchema):
    """Base invoice schema."""
    
    invoice_number: str = Field(..., min_length=1, max_length=50)
    supplier_id: uuid.UUID
    purchase_order_id: Optional[uuid.UUID] = None
    status: str = Field(default="DRAFT")
    invoice_date: datetime
    due_date: Optional[datetime] = None
    currency: str = Field(default="USD", max_length=3)
    payment_terms: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating an invoice."""
    
    lines: List[InvoiceLineCreate] = Field(default_factory=list)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "invoice_number": "INV-2024-001",
                "supplier_id": "550e8400-e29b-41d4-a716-446655440000",
                "purchase_order_id": "660e8400-e29b-41d4-a716-446655440001",
                "status": "DRAFT",
                "invoice_date": "2024-01-20T00:00:00Z",
                "due_date": "2024-02-19T00:00:00Z",
                "currency": "USD",
                "payment_terms": "Net 30",
                "notes": "Monthly billing",
                "lines": [
                    {
                        "line_number": 1,
                        "purchase_order_line_id": "770e8400-e29b-41d4-a716-446655440002",
                        "item_code": "ITEM001",
                        "item_description": "Widget A",
                        "quantity": 50,
                        "unit_of_measure": "EA",
                        "unit_price": 25.00,
                        "tax_rate": 0.10,
                    }
                ],
            }
        }
    )


class InvoiceUpdate(BaseSchema):
    """Schema for updating an invoice."""
    
    invoice_number: Optional[str] = Field(None, min_length=1, max_length=50)
    supplier_id: Optional[uuid.UUID] = None
    purchase_order_id: Optional[uuid.UUID] = None
    status: Optional[str] = None
    invoice_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    currency: Optional[str] = Field(None, max_length=3)
    payment_terms: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    is_archived: Optional[bool] = None


class InvoiceResponse(InvoiceBase):
    """Schema for invoice response."""
    
    id: uuid.UUID
    subtotal: decimal.Decimal
    tax_amount: decimal.Decimal
    total_amount: decimal.Decimal
    amount_paid: decimal.Decimal
    outstanding_amount: decimal.Decimal
    is_archived: bool
    created_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    supplier: Optional[SupplierResponse] = None
    lines: List[InvoiceLineResponse] = Field(default_factory=list)


class InvoiceListResponse(BaseSchema):
    """Schema for paginated invoice list response."""
    
    items: list[InvoiceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool

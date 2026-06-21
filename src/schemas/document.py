// src/schemas/document.py
"""Document and document line schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DocumentLineBase(BaseModel):
    """Base document line schema."""
    line_number: int = Field(..., ge=1)
    sku: Optional[str] = Field(None, max_length=100)
    description: str = Field(..., min_length=1)
    quantity: Decimal = Field(..., gt=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=0)
    tax_rate: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    delivered_quantity: Optional[Decimal] = Field(None, ge=0)


class DocumentLineCreate(DocumentLineBase):
    """Document line creation schema."""
    pass


class DocumentLineResponse(DocumentLineBase):
    """Document line response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    document_id: str
    line_total: Decimal
    tax_amount: Decimal
    matched_quantity: Decimal
    open_quantity: Decimal
    is_fully_matched: bool
    created_at: datetime
    updated_at: datetime


class DocumentBase(BaseModel):
    """Base document schema."""
    document_number: str = Field(..., max_length=100)
    supplier_code: str = Field(..., max_length=100)
    supplier_name: str = Field(..., max_length=255)
    supplier_tax_id: Optional[str] = Field(None, max_length=50)
    reference_number: Optional[str] = Field(None, max_length=100)
    po_reference: Optional[str] = Field(None, max_length=100)
    document_date: date
    expected_delivery_date: Optional[date] = None
    notes: Optional[str] = None
    currency: str = Field(default="USD", max_length=3)


class DocumentResponse(DocumentBase):
    """Document response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    document_type: str
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    open_amount: Decimal
    lines: list[DocumentLineResponse] = []
    created_at: datetime
    updated_at: datetime

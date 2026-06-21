// src/schemas/delivery_note.py
"""Delivery Note schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.document import DocumentLineCreate, DocumentLineResponse


class DeliveryNoteBase(BaseModel):
    """Base delivery note schema."""
    document_number: str = Field(..., max_length=100)
    supplier_code: str = Field(..., max_length=100)
    supplier_name: str = Field(..., max_length=255)
    supplier_tax_id: Optional[str] = Field(None, max_length=50)
    po_reference: Optional[str] = Field(None, max_length=100)
    document_date: date
    delivery_date: Optional[date] = None
    carrier: Optional[str] = Field(None, max_length=255)
    tracking_number: Optional[str] = Field(None, max_length=100)
    delivery_address: Optional[str] = None
    received_by: Optional[str] = Field(None, max_length=255)
    is_partial_delivery: bool = False
    notes: Optional[str] = None
    currency: str = Field(default="USD", max_length=3)


class DeliveryNoteCreate(DeliveryNoteBase):
    """Delivery note creation schema."""
    lines: list[DocumentLineCreate] = Field(..., min_length=1)


class DeliveryNoteUpdate(BaseModel):
    """Delivery note update schema."""
    supplier_code: Optional[str] = Field(None, max_length=100)
    supplier_name: Optional[str] = Field(None, max_length=255)
    delivery_date: Optional[date] = None
    carrier: Optional[str] = Field(None, max_length=255)
    tracking_number: Optional[str] = Field(None, max_length=100)
    delivery_address: Optional[str] = None
    received_by: Optional[str] = Field(None, max_length=255)
    is_partial_delivery: Optional[bool] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class DeliveryNoteResponse(DeliveryNoteBase):
    """Delivery note response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    open_amount: Decimal
    lines: list[DocumentLineResponse] = []
    created_at: datetime
    updated_at: datetime

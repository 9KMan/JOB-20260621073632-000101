// app/schemas/delivery_note.py
"""Delivery Note schemas."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field


class DeliveryNoteLineBase(BaseModel):
    """Base delivery note line schema."""
    line_number: int = Field(..., ge=1)
    product_code: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    quantity_delivered: Decimal = Field(..., ge=0)
    quantity_accepted: Optional[Decimal] = Field(None, ge=0)
    quantity_rejected: Optional[Decimal] = Field(None, ge=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=0)
    line_total: Decimal = Field(..., ge=0)


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating a delivery note line."""
    pass


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """Schema for delivery note line response."""
    id: uuid.UUID
    delivery_note_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class DeliveryNoteBase(BaseModel):
    """Base delivery note schema."""
    dn_number: str = Field(..., min_length=1, max_length=50)
    vendor_id: uuid.UUID
    po_reference: Optional[str] = Field(None, max_length=50)
    delivery_date: date
    received_by: Optional[str] = Field(None, max_length=255)
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating a delivery note."""
    status: str = Field(default="RECEIVED", max_length=20)
    lines: List[DeliveryNoteLineCreate] = Field(default_factory=list)


class DeliveryNoteUpdate(BaseModel):
    """Schema for updating a delivery note."""
    vendor_id: Optional[uuid.UUID] = None
    po_reference: Optional[str] = Field(None, max_length=50)
    delivery_date: Optional[date] = None
    received_by: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(None, max_length=20)
    currency: Optional[str] = Field(None, max_length=3)
    notes: Optional[str] = None
    lines: Optional[List[DeliveryNoteLineCreate]] = None


class DeliveryNoteResponse(DeliveryNoteBase):
    """Schema for delivery note response."""
    id: uuid.UUID
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    created_at: datetime
    updated_at: datetime
    lines: List[DeliveryNoteLineResponse] = []
    
    model_config = {"from_attributes": True}

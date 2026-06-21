// src/app/schemas/delivery_note.py
"""Delivery Note Pydantic schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class DeliveryNoteLineBase(BaseModel):
    """Base delivery note line schema."""
    line_number: int = Field(..., ge=1)
    item_code: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., min_length=1, max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Optional[Decimal] = Field(None, ge=0)


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Delivery note line creation schema."""
    po_line_id: Optional[UUID] = None


class DeliveryNoteLineUpdate(BaseModel):
    """Delivery note line update schema."""
    item_code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    po_line_id: Optional[UUID] = None


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """Delivery note line response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    delivery_note_id: UUID
    po_line_id: Optional[UUID] = None
    line_amount: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime


class DeliveryNoteBase(BaseModel):
    """Base delivery note schema."""
    dn_number: str = Field(..., min_length=1, max_length=50)
    supplier_id: UUID
    supplier_name: str = Field(..., min_length=1, max_length=255)
    po_id: Optional[UUID] = None
    po_number: Optional[str] = Field(None, max_length=50)
    invoice_id: Optional[UUID] = None
    dn_date: date
    received_date: Optional[date] = None
    notes: Optional[str] = None
    currency: str = Field(default="USD", max_length=3)


class DeliveryNoteCreate(DeliveryNoteBase):
    """Delivery note creation schema."""
    lines: List[DeliveryNoteLineCreate] = Field(..., min_length=1)
    status: str = Field(default="pending", max_length=20)


class DeliveryNoteUpdate(BaseModel):
    """Delivery note update schema."""
    supplier_name: Optional[str] = Field(None, max_length=255)
    po_id: Optional[UUID] = None
    po_number: Optional[str] = Field(None, max_length=50)
    invoice_id: Optional[UUID] = None
    dn_date: Optional[date] = None
    received_date: Optional[date] = None
    notes: Optional[str] = None
    status: Optional[str] = Field(None, max_length=20)


class DeliveryNoteResponse(DeliveryNoteBase):
    """Delivery note response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    status: str
    total_amount: Decimal
    total_quantity: Decimal
    matched_amount: Decimal
    open_amount: Decimal
    lines: List[DeliveryNoteLineResponse] = []
    created_at: datetime
    updated_at: datetime

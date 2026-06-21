// src/schemas/delivery_note.py
"""Delivery note schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.models.delivery_note import DeliveryNoteStatus
from src.schemas.common import BaseSchema, TimestampSchema


class DeliveryNoteLineBase(BaseSchema):
    """Base DN line schema."""
    line_number: int
    sku: Optional[str] = None
    description: str = Field(max_length=500)
    quantity: Decimal = Field(gt=0)
    unit_of_measure: str = "EA"


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """DN line creation schema."""
    pass


class DeliveryNoteLineResponse(DeliveryNoteLineBase, TimestampSchema):
    """DN line response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    delivery_note_id: UUID
    line_total: Decimal


class DeliveryNoteBase(BaseSchema):
    """Base delivery note schema."""
    dn_number: str = Field(max_length=50)
    supplier_id: str = Field(max_length=100)
    supplier_name: str = Field(max_length=255)
    supplier_reference: Optional[str] = None
    po_reference: Optional[str] = None
    delivery_date: str
    received_date: Optional[str] = None
    currency: str = "USD"
    notes: Optional[str] = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Delivery note creation schema."""
    lines: list[DeliveryNoteLineCreate]


class DeliveryNoteUpdate(BaseSchema):
    """Delivery note update schema."""
    supplier_name: Optional[str] = None
    supplier_reference: Optional[str] = None
    received_date: Optional[str] = None
    status: Optional[DeliveryNoteStatus] = None
    notes: Optional[str] = None
    lines: Optional[list[DeliveryNoteLineCreate]] = None


class DeliveryNoteResponse(DeliveryNoteBase, TimestampSchema):
    """Delivery note response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    total_amount: Decimal
    status: DeliveryNoteStatus
    lines: list[DeliveryNoteLineResponse] = []

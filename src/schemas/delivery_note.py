// src/schemas/delivery_note.py
"""Delivery Note schemas."""
from typing import Optional, List
from datetime import date
from decimal import Decimal
from uuid import UUID
from pydantic import Field, ConfigDict

from src.schemas.base import BaseSchema, TimestampUUIDSchema
from src.models.enums import DocumentStatus


class DeliveryNoteLineBase(BaseSchema):
    """Base DN line schema."""
    
    line_number: int = Field(..., ge=1)
    product_code: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., min_length=1, max_length=500)
    quantity_delivered: Decimal = Field(..., gt=0)
    quantity_accepted: Optional[Decimal] = None
    quantity_rejected: Decimal = Field(default=Decimal("0.000"), ge=0)
    unit_of_measure: str = Field(default="EA", max_length=20)


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating a DN line."""
    pass


class DeliveryNoteLineResponse(TimestampUUIDSchema):
    """Schema for DN line response."""
    
    delivery_note_id: UUID
    line_number: int
    product_code: str
    description: str
    quantity_delivered: Decimal
    quantity_accepted: Optional[Decimal] = None
    quantity_rejected: Decimal
    unit_of_measure: str


class DeliveryNoteBase(BaseSchema):
    """Base DN schema."""
    
    dn_number: str = Field(..., min_length=1, max_length=50)
    supplier_id: UUID
    po_id: Optional[UUID] = None
    delivery_date: date
    received_by: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = Field(None, max_length=1000)


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating a DN."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    lines: List[DeliveryNoteLineCreate] = Field(..., min_length=1)


class DeliveryNoteUpdate(BaseSchema):
    """Schema for updating a DN."""
    
    dn_number: Optional[str] = Field(None, min_length=1, max_length=50)
    supplier_id: Optional[UUID] = None
    po_id: Optional[UUID] = None
    delivery_date: Optional[date] = None
    received_by: Optional[str] = Field(None, max_length=255)
    status: Optional[DocumentStatus] = None
    notes: Optional[str] = Field(None, max_length=1000)


class DeliveryNoteResponse(TimestampUUIDSchema):
    """Schema for DN response."""
    
    dn_number: str
    supplier_id: UUID
    po_id: Optional[UUID] = None
    delivery_date: date
    received_by: Optional[str] = None
    status: DocumentStatus
    notes: Optional[str] = None
    lines: List[DeliveryNoteLineResponse] = []


class DeliveryNoteListResponse(BaseSchema):
    """Schema for DN list response without lines."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    dn_number: str
    supplier_id: UUID
    po_id: Optional[UUID] = None
    delivery_date: date
    received_by: Optional[str] = None
    status: DocumentStatus
    created_at: date
    updated_at: date

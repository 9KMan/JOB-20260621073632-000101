// api/schemas/delivery_note.py
"""Delivery Note schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


class DeliveryNoteLineBase(BaseModel):
    """Base delivery note line schema."""
    
    line_number: int = Field(..., ge=1)
    item_code: Optional[str] = Field(None, max_length=100)
    description: str = Field(..., min_length=1)
    quantity_ordered: Optional[Decimal] = Field(None, gt=0)
    quantity_delivered: Decimal = Field(..., gt=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    po_line_id: Optional[UUID] = None
    notes: Optional[str] = None


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating a delivery note line."""
    pass


class DeliveryNoteLineUpdate(BaseModel):
    """Schema for updating a delivery note line."""
    
    item_code: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    quantity_ordered: Optional[Decimal] = Field(None, gt=0)
    quantity_delivered: Optional[Decimal] = Field(None, gt=0)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    po_line_id: Optional[UUID] = None
    notes: Optional[str] = None


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """Schema for delivery note line response."""
    
    id: UUID
    delivery_note_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class DeliveryNoteBase(BaseModel):
    """Base delivery note schema."""
    
    dn_number: str = Field(..., min_length=1, max_length=100)
    supplier_id: UUID
    po_id: Optional[UUID] = None
    delivery_date: date
    received_by: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating a delivery note."""
    
    lines: List[DeliveryNoteLineCreate] = Field(default_factory=list)


class DeliveryNoteUpdate(BaseModel):
    """Schema for updating a delivery note."""
    
    supplier_id: Optional[UUID] = None
    po_id: Optional[UUID] = None
    delivery_date: Optional[date] = None
    received_by: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = None
    notes: Optional[str] = None


class DeliveryNoteResponse(DeliveryNoteBase):
    """Schema for delivery note response."""
    
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class DeliveryNoteDetailResponse(DeliveryNoteResponse):
    """Schema for detailed delivery note response with lines."""
    
    lines: List[DeliveryNoteLineResponse] = []
    
    model_config = {"from_attributes": True}

// src/schemas/delivery_note.py
"""Delivery Note schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DeliveryNoteLineBase(BaseModel):
    """Base delivery note line schema."""
    
    line_number: int = Field(..., ge=1)
    item_code: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    quantity_ordered: Optional[Decimal] = Field(None, ge=0)
    quantity_delivered: Decimal = Field(..., ge=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    condition: str = Field(default="good", max_length=50)
    notes: Optional[str] = None


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Delivery note line creation schema."""
    pass


class DeliveryNoteLineUpdate(BaseModel):
    """Delivery note line update schema."""
    
    item_code: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    quantity_ordered: Optional[Decimal] = Field(None, ge=0)
    quantity_delivered: Optional[Decimal] = Field(None, ge=0)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    condition: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class DeliveryNoteLineResponse(BaseModel):
    """Delivery note line response schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    line_number: int
    item_code: str
    description: str
    quantity_ordered: Optional[Decimal] = None
    quantity_delivered: Decimal
    unit_of_measure: str
    condition: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DeliveryNoteBase(BaseModel):
    """Base delivery note schema."""
    
    dn_number: str = Field(..., min_length=1, max_length=100)
    vendor_id: UUID
    po_reference: Optional[str] = Field(None, max_length=50)
    delivery_date: date
    received_by: Optional[str] = Field(None, max_length=255)
    status: str = Field(default="pending", max_length=50)
    notes: Optional[str] = None
    attachments: Optional[str] = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Delivery note creation schema."""
    
    lines: List[DeliveryNoteLineCreate] = Field(default_factory=list)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "dn_number": "DN-2024-001",
                "vendor_id": "uuid-here",
                "po_reference": "PO-2024-001",
                "delivery_date": "2024-01-25",
                "received_by": "John Smith",
                "status": "pending",
                "notes": "All items in good condition",
                "lines": []
            }
        }
    )


class DeliveryNoteUpdate(BaseModel):
    """Delivery note update schema."""
    
    dn_number: Optional[str] = Field(None, min_length=1, max_length=100)
    vendor_id: Optional[UUID] = None
    po_reference: Optional[str] = Field(None, max_length=50)
    delivery_date: Optional[date] = None
    received_by: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None
    attachments: Optional[str] = None


class DeliveryNoteResponse(BaseModel):
    """Delivery note response schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    dn_number: str
    vendor_id: UUID
    po_reference: Optional[str] = None
    delivery_date: date
    received_by: Optional[str] = None
    status: str
    notes: Optional[str] = None
    attachments: Optional[str] = None
    received_at: datetime
    created_at: datetime
    updated_at: datetime
    lines: List[DeliveryNoteLineResponse] = Field(default_factory=list)

# src/schemas/delivery_note.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


class DeliveryNoteLineBase(BaseModel):
    """Base schema for Delivery Note line."""
    line_number: int = Field(..., ge=1)
    product_code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    quantity_delivered: Decimal = Field(..., ge=0)
    quantity_accepted: Optional[Decimal] = Field(None, ge=0)
    quantity_rejected: Optional[Decimal] = Field(None, ge=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    po_line_reference: Optional[str] = Field(None, max_length=36)
    notes: Optional[str] = Field(None, max_length=500)


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating Delivery Note line."""
    pass


class DeliveryNoteLineUpdate(BaseModel):
    """Schema for updating Delivery Note line."""
    line_number: Optional[int] = Field(None, ge=1)
    product_code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    quantity_delivered: Optional[Decimal] = Field(None, ge=0)
    quantity_accepted: Optional[Decimal] = Field(None, ge=0)
    quantity_rejected: Optional[Decimal] = Field(None, ge=0)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    po_line_reference: Optional[str] = Field(None, max_length=36)
    notes: Optional[str] = Field(None, max_length=500)


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """Schema for Delivery Note line response."""
    id: str
    delivery_note_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeliveryNoteBase(BaseModel):
    """Base schema for Delivery Note."""
    dn_number: str = Field(..., max_length=50)
    supplier_id: str = Field(..., max_length=36)
    supplier_name: str = Field(..., max_length=255)
    supplier_code: Optional[str] = Field(None, max_length=50)
    po_reference: Optional[str] = Field(None, max_length=50)
    delivery_date: date
    received_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = Field(None, max_length=1000)
    metadata: Optional[str] = Field(None, max_length=5000)


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating Delivery Note."""
    lines: List[DeliveryNoteLineCreate] = Field(default_factory=list)


class DeliveryNoteUpdate(BaseModel):
    """Schema for updating Delivery Note."""
    supplier_name: Optional[str] = Field(None, max_length=255)
    supplier_code: Optional[str] = Field(None, max_length=50)
    po_reference: Optional[str] = Field(None, max_length=50)
    received_date: Optional[date] = None
    status: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=1000)
    metadata: Optional[str] = Field(None, max_length=5000)


class DeliveryNoteResponse(DeliveryNoteBase):
    """Schema for Delivery Note response."""
    id: str
    status: str
    total_amount: Decimal
    created_at: datetime
    updated_at: datetime
    lines: List[DeliveryNoteLineResponse] = []

    class Config:
        from_attributes = True

// src/schemas/delivery_note.py
"""Delivery Note schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DeliveryNoteLineBase(BaseModel):
    """Base schema for delivery note line."""
    line_number: int
    sku: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    quantity_delivered: Decimal = Field(..., gt=0)
    quantity_received: Decimal = Field(default=Decimal("0"), ge=0)
    unit_price: Decimal = Field(..., ge=0)
    line_total: Decimal = Field(..., ge=0)


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating a delivery note line."""
    pass


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """Schema for delivery note line response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    delivery_note_id: UUID
    created_at: datetime
    updated_at: datetime


class DeliveryNoteLineUpdate(BaseModel):
    """Schema for updating a delivery note line."""
    sku: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    quantity_delivered: Optional[Decimal] = Field(None, gt=0)
    quantity_received: Optional[Decimal] = Field(None, ge=0)
    unit_price: Optional[Decimal] = Field(None, ge=0)


class DeliveryNoteBase(BaseModel):
    """Base schema for Delivery Note."""
    dn_number: str = Field(..., max_length=100)
    supplier_id: str = Field(..., max_length=100)
    supplier_name: str = Field(..., max_length=255)
    po_reference: Optional[str] = Field(None, max_length=100)
    currency: str = Field(default="USD", max_length=3)
    total_amount: Decimal = Field(..., ge=0)
    delivery_date: date
    received_by: Optional[str] = Field(None, max_length=255)


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating a Delivery Note."""
    lines: list[DeliveryNoteLineCreate] = Field(default_factory=list)


class DeliveryNoteUpdate(BaseModel):
    """Schema for updating a Delivery Note."""
    supplier_id: Optional[str] = Field(None, max_length=100)
    supplier_name: Optional[str] = Field(None, max_length=255)
    po_reference: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, max_length=50)
    currency: Optional[str] = Field(None, max_length=3)
    total_amount: Optional[Decimal] = Field(None, ge=0)
    received_by: Optional[str] = Field(None, max_length=255)


class DeliveryNoteResponse(DeliveryNoteBase):
    """Schema for Delivery Note response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    lines: list[DeliveryNoteLineResponse] = Field(default_factory=list)


class DeliveryNoteListResponse(BaseModel):
    """Schema for paginated delivery note list."""
    items: list[DeliveryNoteResponse]
    total: int
    page: int
    page_size: int
    pages: int

// src/schemas/delivery_note.py
"""Delivery Note schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DeliveryNoteLineItemBase(BaseModel):
    """Base line item schema."""
    line_number: int = Field(..., ge=1)
    item_code: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=0)
    line_total: Decimal = Field(..., ge=0)


class DeliveryNoteLineItemCreate(DeliveryNoteLineItemBase):
    """Schema for line item creation."""
    pass


class DeliveryNoteLineItemResponse(DeliveryNoteLineItemBase):
    """Schema for line item response."""
    id: UUID
    delivery_note_id: UUID
    
    model_config = {"from_attributes": True}


class DeliveryNoteBase(BaseModel):
    """Base delivery note schema."""
    dn_number: str = Field(..., max_length=50)
    supplier_id: UUID
    purchase_order_id: Optional[UUID] = None
    delivery_date: date
    received_by: str = Field(..., max_length=100)
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for delivery note creation."""
    line_items: list[DeliveryNoteLineItemCreate] = Field(default_factory=list)


class DeliveryNoteUpdate(BaseModel):
    """Schema for delivery note update."""
    dn_number: Optional[str] = Field(None, max_length=50)
    supplier_id: Optional[UUID] = None
    purchase_order_id: Optional[UUID] = None
    delivery_date: Optional[date] = None
    received_by: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, max_length=20)
    currency: Optional[str] = Field(None, max_length=3)
    notes: Optional[str] = None
    line_items: Optional[list[DeliveryNoteLineItemCreate]] = None


class DeliveryNoteResponse(DeliveryNoteBase):
    """Schema for delivery note response."""
    id: UUID
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    line_items: list[DeliveryNoteLineItemResponse] = []
    
    model_config = {"from_attributes": True}


class DeliveryNoteListResponse(BaseModel):
    """Schema for paginated delivery note list."""
    items: list[DeliveryNoteResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

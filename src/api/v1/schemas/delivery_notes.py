# src/api/v1/schemas/delivery_notes.py
"""Delivery Note schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DeliveryNoteLineBase(BaseModel):
    """Base delivery note line schema."""
    line_number: int
    item_code: str = Field(..., max_length=100)
    item_description: str = Field(..., max_length=500)
    quantity: Decimal = Field(..., gt=0)
    quantity_received: Decimal = Field(..., ge=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=0)
    line_total: Decimal = Field(..., ge=0)


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Delivery note line creation schema."""
    purchase_order_line_id: Optional[UUID] = None


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """Delivery note line response schema."""
    id: UUID
    delivery_note_id: UUID
    purchase_order_line_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DeliveryNoteBase(BaseModel):
    """Base delivery note schema."""
    dn_number: str = Field(..., max_length=50)
    supplier_id: str = Field(..., max_length=100)
    supplier_name: str = Field(..., max_length=255)
    supplier_reference: Optional[str] = Field(None, max_length=100)
    po_reference: Optional[str] = Field(None, max_length=50)
    delivery_date: date
    received_by: Optional[str] = Field(None, max_length=255)
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Delivery note creation schema."""
    lines: list[DeliveryNoteLineCreate] = Field(..., min_length=1)


class DeliveryNoteUpdate(BaseModel):
    """Delivery note update schema."""
    supplier_name: Optional[str] = Field(None, max_length=255)
    supplier_reference: Optional[str] = Field(None, max_length=100)
    received_by: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = None
    notes: Optional[str] = None


class DeliveryNoteResponse(DeliveryNoteBase):
    """Delivery note response schema."""
    id: UUID
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DeliveryNoteDetailResponse(DeliveryNoteResponse):
    """Delivery note detail response schema with lines."""
    lines: list[DeliveryNoteLineResponse] = []

    model_config = {"from_attributes": True}

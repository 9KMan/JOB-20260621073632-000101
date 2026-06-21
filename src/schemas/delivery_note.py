# src/schemas/delivery_note.py
"""Delivery Note schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DeliveryNoteLineBase(BaseModel):
    """Base delivery note line schema."""
    line_number: int
    item_code: Optional[str] = None
    item_description: str = Field(max_length=500)
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    line_amount: Decimal = Field(ge=0)
    uom: Optional[str] = None


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Delivery note line creation schema."""
    pass


class DeliveryNoteLineUpdate(BaseModel):
    """Delivery note line update schema."""
    line_number: Optional[int] = None
    item_code: Optional[str] = None
    item_description: Optional[str] = None
    quantity: Optional[Decimal] = Field(default=None, gt=0)
    unit_price: Optional[Decimal] = Field(default=None, ge=0)
    line_amount: Optional[Decimal] = Field(default=None, ge=0)
    uom: Optional[str] = None


class DeliveryNoteLineInDB(DeliveryNoteLineBase):
    """Delivery note line database schema."""
    id: UUID
    delivery_note_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """Delivery note line response schema."""
    id: UUID
    delivery_note_id: UUID

    model_config = ConfigDict(from_attributes=True)


class DeliveryNoteBase(BaseModel):
    """Base delivery note schema."""
    dn_number: str = Field(max_length=100)
    supplier_id: str = Field(max_length=100)
    supplier_name: str = Field(max_length=255)
    dn_date: date
    received_date: Optional[date] = None
    total_amount: Decimal = Field(gt=0)
    currency: str = Field(default="USD", max_length=3)
    status: str = Field(default="pending", max_length=50)
    notes: Optional[str] = Field(default=None, max_length=1000)
    purchase_order_id: Optional[UUID] = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Delivery note creation schema."""
    line_items: List[DeliveryNoteLineCreate] = []


class DeliveryNoteUpdate(BaseModel):
    """Delivery note update schema."""
    dn_number: Optional[str] = Field(default=None, max_length=100)
    supplier_id: Optional[str] = Field(default=None, max_length=100)
    supplier_name: Optional[str] = Field(default=None, max_length=255)
    dn_date: Optional[date] = None
    received_date: Optional[date] = None
    total_amount: Optional[Decimal] = Field(default=None, gt=0)
    currency: Optional[str] = Field(default=None, max_length=3)
    status: Optional[str] = Field(default=None, max_length=50)
    notes: Optional[str] = Field(default=None, max_length=1000)
    purchase_order_id: Optional[UUID] = None
    line_items: Optional[List[DeliveryNoteLineCreate]] = None


class DeliveryNoteInDB(DeliveryNoteBase):
    """Delivery note database schema."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeliveryNoteResponse(DeliveryNoteBase):
    """Delivery note response schema."""
    id: UUID
    line_items: List[DeliveryNoteLineResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeliveryNoteListResponse(BaseModel):
    """Delivery note list response schema."""
    items: List[DeliveryNoteResponse]
    total: int
    page: int
    page_size: int

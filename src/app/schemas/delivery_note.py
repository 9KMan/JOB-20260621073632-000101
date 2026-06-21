// src/app/schemas/delivery_note.py
"""Delivery Note schemas."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict


class DeliveryNoteLineBase(BaseModel):
    """Base schema for Delivery Note line."""

    line_number: int
    product_code: Optional[str] = None
    product_description: str
    quantity_delivered: Decimal
    quantity_accepted: Optional[Decimal] = None
    quantity_rejected: Optional[Decimal] = None
    unit_of_measure: str = "EA"
    metadata: Optional[dict] = None


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating a DN line."""

    pass


class DeliveryNoteLineUpdate(BaseModel):
    """Schema for updating a DN line."""

    line_number: Optional[int] = None
    product_code: Optional[str] = None
    product_description: Optional[str] = None
    quantity_delivered: Optional[Decimal] = None
    quantity_accepted: Optional[Decimal] = None
    quantity_rejected: Optional[Decimal] = None
    unit_of_measure: Optional[str] = None
    metadata: Optional[dict] = None


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """Schema for DN line response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    delivery_note_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class DeliveryNoteBase(BaseModel):
    """Base schema for Delivery Note."""

    dn_number: str
    supplier_id: str
    supplier_name: str
    po_reference: Optional[str] = None
    delivery_date: date
    received_by: Optional[str] = None
    currency: str = "USD"
    notes: Optional[str] = None
    metadata: Optional[dict] = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating a Delivery Note."""

    lines: List[DeliveryNoteLineCreate] = Field(default_factory=list)


class DeliveryNoteUpdate(BaseModel):
    """Schema for updating a Delivery Note."""

    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    status: Optional[str] = None
    received_by: Optional[str] = None
    currency: Optional[str] = None
    notes: Optional[str] = None
    metadata: Optional[dict] = None


class DeliveryNoteResponse(DeliveryNoteBase):
    """Schema for Delivery Note response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    subtotal: Decimal
    total_amount: Decimal
    lines: List[DeliveryNoteLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class DeliveryNoteListResponse(BaseModel):
    """Schema for paginated DN list."""

    items: List[DeliveryNoteResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

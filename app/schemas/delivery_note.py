# app/schemas/delivery_note.py
"""Delivery Note schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class DeliveryNoteLineBase(BaseModel):
    """Base delivery note line schema."""

    line_number: int = Field(..., ge=1)
    product_code: Optional[str] = Field(None, max_length=100)
    description: str = Field(..., min_length=1)
    quantity_ordered: Decimal = Field(..., ge=0)
    quantity_delivered: Decimal = Field(..., ge=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=0)
    notes: Optional[str] = None


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Delivery note line creation request."""

    pass


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """Delivery note line response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    line_total: Decimal
    created_at: datetime
    updated_at: datetime


class DeliveryNoteBase(BaseModel):
    """Base delivery note schema."""

    dn_number: str = Field(..., min_length=1, max_length=50)
    vendor_id: str
    po_reference: Optional[str] = Field(None, max_length=50)
    delivery_date: str
    received_by: Optional[str] = Field(None, max_length=255)
    currency: str = Field(default="USD", max_length=3)
    warehouse_location: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Delivery note creation request."""

    lines: List[DeliveryNoteLineCreate]
    status: str = Field(default="submitted")


class DeliveryNoteUpdate(BaseModel):
    """Delivery note update request."""

    dn_number: Optional[str] = Field(None, min_length=1, max_length=50)
    vendor_id: Optional[str] = None
    po_reference: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = None
    delivery_date: Optional[str] = None
    received_by: Optional[str] = Field(None, max_length=255)
    currency: Optional[str] = Field(None, max_length=3)
    warehouse_location: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class DeliveryNoteResponse(DeliveryNoteBase):
    """Delivery note response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    subtotal: Decimal
    total_amount: Decimal
    created_at: datetime
    updated_at: datetime
    lines: List[DeliveryNoteLineResponse] = []


class DeliveryNoteListResponse(BaseModel):
    """Delivery note list response with pagination."""

    items: List[DeliveryNoteResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

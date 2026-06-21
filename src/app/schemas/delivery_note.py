// src/app/schemas/delivery_note.py
"""Delivery Note Pydantic schemas."""

from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field

from src.app.schemas.supplier import SupplierResponse


class DeliveryNoteLineBase(BaseModel):
    """Base delivery note line schema."""

    line_number: int = Field(..., ge=1)
    item_code: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    line_total: Decimal = Field(..., ge=0)
    uom: Optional[str] = Field(None, max_length=20)


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating a delivery note line."""

    pass


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """Schema for delivery note line response."""

    id: str
    delivery_note_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeliveryNoteBase(BaseModel):
    """Base delivery note schema."""

    dn_number: str = Field(..., min_length=1, max_length=50)
    po_reference: Optional[str] = Field(None, max_length=50)
    supplier_id: str
    delivery_date: date
    total_amount: Decimal = Field(..., ge=0)
    currency: str = Field(default="USD", max_length=3)
    status: str = Field(default="RECEIVED", max_length=20)
    notes: Optional[str] = Field(None, max_length=1000)


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating a delivery note."""

    lines: List[DeliveryNoteLineCreate] = Field(..., min_length=1)


class DeliveryNoteUpdate(BaseModel):
    """Schema for updating a delivery note."""

    status: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = Field(None, max_length=1000)


class DeliveryNoteResponse(DeliveryNoteBase):
    """Schema for delivery note response."""

    id: str
    created_at: datetime
    updated_at: datetime
    lines: List[DeliveryNoteLineResponse] = []
    supplier: Optional[SupplierResponse] = None

    class Config:
        from_attributes = True


class DeliveryNoteListResponse(BaseModel):
    """Schema for paginated delivery note list response."""

    items: List[DeliveryNoteResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

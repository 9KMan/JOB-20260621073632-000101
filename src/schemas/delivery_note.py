// src/schemas/delivery_note.py
"""Delivery Note schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import Field, ConfigDict

from src.schemas.common import BaseSchema
from src.schemas.supplier import SupplierResponse
from src.models.enums import DocumentStatus


class DeliveryNoteLineBase(BaseSchema):
    """Base DN line schema."""
    line_number: int = Field(..., ge=1)
    product_code: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    quantity_delivered: Decimal = Field(..., ge=0)
    quantity_accepted: Optional[Decimal] = Field(None, ge=0)
    quantity_rejected: Decimal = Field(default=Decimal("0.0000"), ge=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=0)


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """DN line creation schema."""
    pass


class DeliveryNoteLineUpdate(BaseSchema):
    """DN line update schema."""
    line_number: Optional[int] = Field(None, ge=1)
    product_code: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    quantity_delivered: Optional[Decimal] = Field(None, ge=0)
    quantity_accepted: Optional[Decimal] = Field(None, ge=0)
    quantity_rejected: Optional[Decimal] = Field(None, ge=0)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    unit_price: Optional[Decimal] = Field(None, ge=0)


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """DN line response schema."""
    id: UUID
    delivery_note_id: UUID
    line_total: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeliveryNoteBase(BaseSchema):
    """Base DN schema."""
    delivery_note_number: str = Field(..., min_length=1, max_length=50)
    supplier_id: UUID
    po_reference: Optional[str] = Field(None, max_length=50)
    delivery_date: date
    received_by: Optional[str] = Field(None, max_length=255)
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None
    attachment_url: Optional[str] = Field(None, max_length=500)


class DeliveryNoteCreate(DeliveryNoteBase):
    """DN creation schema."""
    lines: list[DeliveryNoteLineCreate] = Field(default_factory=list)


class DeliveryNoteUpdate(BaseSchema):
    """DN update schema."""
    delivery_note_number: Optional[str] = Field(None, min_length=1, max_length=50)
    supplier_id: Optional[UUID] = None
    po_reference: Optional[str] = Field(None, max_length=50)
    delivery_date: Optional[date] = None
    received_by: Optional[str] = Field(None, max_length=255)
    status: Optional[DocumentStatus] = None
    currency: Optional[str] = Field(None, max_length=3)
    notes: Optional[str] = None
    attachment_url: Optional[str] = Field(None, max_length=500)


class DeliveryNoteResponse(DeliveryNoteBase):
    """DN response schema."""
    id: UUID
    status: DocumentStatus
    subtotal: Decimal
    created_at: datetime
    updated_at: datetime
    lines: list[DeliveryNoteLineResponse] = Field(default_factory=list)
    supplier: Optional[SupplierResponse] = None

    model_config = ConfigDict(from_attributes=True)

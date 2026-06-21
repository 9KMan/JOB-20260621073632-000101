# src/app/schemas/delivery_note.py
"""Delivery Note schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.app.schemas.common import BaseSchema, TimestampMixin, UUIDMixin
from src.app.models.enums import DocumentStatus, LineStatus


class DeliveryNoteLineBase(BaseSchema):
    """Base DN line schema."""
    line_number: int = Field(..., ge=1)
    description: str = Field(..., min_length=1, max_length=500)
    sku: Optional[str] = Field(None, max_length=100)
    quantity_delivered: Decimal = Field(..., ge=0)
    status: LineStatus = Field(default=LineStatus.PENDING)


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating a DN line."""
    pass


class DeliveryNoteLineUpdate(BaseSchema):
    """Schema for updating a DN line."""
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    sku: Optional[str] = Field(None, max_length=100)
    quantity_delivered: Optional[Decimal] = Field(None, ge=0)
    status: Optional[LineStatus] = None


class DeliveryNoteLineRead(UUIDMixin, TimestampMixin, DeliveryNoteLineBase):
    """Schema for reading a DN line."""
    dn_id: UUID
    deleted_at: Optional[datetime] = None
    is_deleted: bool = False


class DeliveryNoteBase(BaseSchema):
    """Base DN schema."""
    supplier_id: str = Field(..., min_length=1, max_length=100)
    supplier_name: str = Field(..., min_length=1, max_length=255)
    dn_number: str = Field(..., min_length=1, max_length=100)
    dn_date: date
    receipt_date: Optional[date] = None
    currency: str = Field(default="USD", min_length=3, max_length=3)
    total_amount: Decimal = Field(..., ge=0)
    status: DocumentStatus = Field(default=DocumentStatus.RECEIVED)
    notes: Optional[str] = None
    metadata: Optional[dict] = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating a DN."""
    lines: list[DeliveryNoteLineCreate] = Field(default_factory=list)


class DeliveryNoteUpdate(BaseSchema):
    """Schema for updating a DN."""
    supplier_id: Optional[str] = Field(None, min_length=1, max_length=100)
    supplier_name: Optional[str] = Field(None, min_length=1, max_length=255)
    dn_number: Optional[str] = Field(None, min_length=1, max_length=100)
    dn_date: Optional[date] = None
    receipt_date: Optional[date] = None
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    total_amount: Optional[Decimal] = Field(None, ge=0)
    status: Optional[DocumentStatus] = None
    notes: Optional[str] = None
    metadata: Optional[dict] = None


class DeliveryNoteRead(UUIDMixin, TimestampMixin, DeliveryNoteBase):
    """Schema for reading a DN."""
    deleted_at: Optional[datetime] = None
    is_deleted: bool = False
    lines: list[DeliveryNoteLineRead] = Field(default_factory=list)

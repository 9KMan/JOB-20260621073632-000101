// src/schemas/delivery_note.py
"""Delivery Note schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from src.schemas.common import BaseSchema, UUIDMixin


class DeliveryNoteLineBase(BaseModel):
    """Base schema for delivery note line items."""
    line_number: int
    sku: Optional[str] = None
    description: str
    quantity: Decimal
    uom: str = "EA"
    po_line_id: Optional[UUID] = None
    metadata: Optional[dict] = None


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating delivery note line items."""
    pass


class DeliveryNoteLineUpdate(BaseModel):
    """Schema for updating delivery note line items."""
    sku: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[Decimal] = None
    uom: Optional[str] = None
    po_line_id: Optional[UUID] = None
    metadata: Optional[dict] = None


class DeliveryNoteLineResponse(UUIDMixin, BaseSchema):
    """Response schema for delivery note line items."""
    delivery_note_id: UUID
    line_number: int
    sku: Optional[str]
    description: str
    quantity: Decimal
    uom: str
    po_line_id: Optional[UUID]
    metadata: Optional[dict]
    created_at: datetime
    updated_at: datetime


class DeliveryNoteBase(BaseModel):
    """Base schema for delivery notes."""
    dn_number: str = Field(max_length=50)
    supplier_id: str = Field(max_length=100)
    supplier_name: str = Field(max_length=255)
    supplier_reference: Optional[str] = None
    delivery_date: date
    received_by: Optional[str] = None
    total_quantity: Decimal = Decimal("0")
    status: str = "RECEIVED"
    notes: Optional[str] = None
    metadata: Optional[dict] = None
    purchase_order_id: Optional[UUID] = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating a delivery note."""
    lines: list[DeliveryNoteLineCreate] = Field(default_factory=list)


class DeliveryNoteUpdate(BaseModel):
    """Schema for updating a delivery note."""
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    supplier_reference: Optional[str] = None
    delivery_date: Optional[date] = None
    received_by: Optional[str] = None
    total_quantity: Optional[Decimal] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    metadata: Optional[dict] = None
    purchase_order_id: Optional[UUID] = None


class DeliveryNoteResponse(UUIDMixin, BaseSchema):
    """Response schema for delivery notes."""
    dn_number: str
    supplier_id: str
    supplier_name: str
    supplier_reference: Optional[str]
    delivery_date: date
    received_by: Optional[str]
    total_quantity: Decimal
    status: str
    notes: Optional[str]
    metadata: Optional[dict]
    purchase_order_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    is_deleted: bool


class DeliveryNoteListResponse(BaseSchema):
    """Response schema for listing delivery notes."""
    id: UUID
    dn_number: str
    supplier_id: str
    supplier_name: str
    delivery_date: date
    total_quantity: Decimal
    status: str
    created_at: datetime

// src/schemas/delivery_note.py
"""Delivery Note schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from src.schemas.common import BaseSchema, TimestampMixin


class DeliveryNoteLineBase(BaseSchema):
    """Base delivery note line schema."""
    line_number: int
    item_code: str
    item_description: str
    ordered_quantity: Decimal = Decimal("0.00")
    delivered_quantity: Decimal
    accepted_quantity: Decimal = Decimal("0.00")
    rejected_quantity: Decimal = Decimal("0.00")
    unit_of_measure: str = "EA"


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating a delivery note line."""
    po_line_id: Optional[UUID] = None


class DeliveryNoteLineUpdate(BaseSchema):
    """Schema for updating a delivery note line."""
    item_code: Optional[str] = None
    item_description: Optional[str] = None
    ordered_quantity: Optional[Decimal] = None
    delivered_quantity: Optional[Decimal] = None
    accepted_quantity: Optional[Decimal] = None
    rejected_quantity: Optional[Decimal] = None
    unit_of_measure: Optional[str] = None
    po_line_id: Optional[UUID] = None
    matched_quantity: Optional[Decimal] = None


class DeliveryNoteLineResponse(DeliveryNoteLineBase, TimestampMixin):
    """Schema for delivery note line response."""
    id: UUID
    delivery_note_id: UUID
    po_line_id: Optional[UUID] = None
    matched_quantity: Decimal
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DeliveryNoteBase(BaseSchema):
    """Base delivery note schema."""
    delivery_note_number: str
    supplier_id: str
    supplier_name: str
    supplier_code: Optional[str] = None
    delivery_date: date
    received_date: Optional[date] = None
    po_reference: Optional[str] = None
    waybill_number: Optional[str] = None
    carrier_name: Optional[str] = None
    notes: Optional[str] = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating a delivery note."""
    lines: list[DeliveryNoteLineCreate]
    created_by_id: Optional[UUID] = None


class DeliveryNoteUpdate(BaseSchema):
    """Schema for updating a delivery note."""
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    received_date: Optional[date] = None
    status: Optional[str] = None
    po_reference: Optional[str] = None
    waybill_number: Optional[str] = None
    carrier_name: Optional[str] = None
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None


class DeliveryNoteResponse(DeliveryNoteBase, TimestampMixin):
    """Schema for delivery note response."""
    id: UUID
    status: str
    po_id: Optional[UUID] = None
    rejection_reason: Optional[str] = None
    created_by_id: Optional[UUID] = None
    received_by_id: Optional[UUID] = None
    approved_by_id: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    lines: list[DeliveryNoteLineResponse] = []

    model_config = ConfigDict(from_attributes=True)


class DeliveryNoteSummary(BaseSchema):
    """Summary of delivery note for lists."""
    id: UUID
    delivery_note_number: str
    supplier_name: str
    delivery_date: date
    status: str
    po_reference: Optional[str] = None
    match_status: str = "unmatched"

    model_config = ConfigDict(from_attributes=True)

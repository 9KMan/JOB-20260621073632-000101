"""Delivery note schemas."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.models.delivery_note import DeliveryNoteStatus


class DeliveryNoteLineBase(BaseModel):
    line_number: int = Field(ge=1)
    sku: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=512)
    quantity_received: Decimal = Field(ge=Decimal("0"))
    uom: str = Field(default="EA", min_length=1, max_length=16)


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    pass


class DeliveryNoteLineRead(DeliveryNoteLineBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class DeliveryNoteBase(BaseModel):
    delivery_number: str = Field(min_length=1, max_length=64)
    supplier_id: UUID
    delivery_date: date
    po_number: str | None = Field(default=None, max_length=64)
    received_by: str | None = Field(default=None, max_length=128)


class DeliveryNoteCreate(DeliveryNoteBase):
    lines: list[DeliveryNoteLineCreate] = Field(default_factory=list)


class DeliveryNoteRead(DeliveryNoteBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: DeliveryNoteStatus
    created_at: datetime
    updated_at: datetime
    lines: list[DeliveryNoteLineRead] = Field(default_factory=list)

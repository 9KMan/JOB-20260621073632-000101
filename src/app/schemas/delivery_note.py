// src/app/schemas/delivery_note.py
"""Delivery Note schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import BaseSchema, TimestampMixin, UUIDMixin


class DeliveryNoteLineBase(BaseModel):
    """Delivery Note Line base schema."""

    line_number: int = Field(ge=1)
    product_code: str = Field(max_length=100)
    product_description: str = Field(max_length=500)
    quantity: Decimal = Field(ge=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    line_amount: Decimal = Field(ge=0)
    matched_quantity: Decimal = Field(default=Decimal("0.00"), ge=0)


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Delivery Note Line creation schema."""

    pass


class DeliveryNoteLineUpdate(BaseModel):
    """Delivery Note Line update schema."""

    product_code: Optional[str] = Field(default=None, max_length=100)
    product_description: Optional[str] = Field(default=None, max_length=500)
    quantity: Optional[Decimal] = Field(default=None, ge=0)
    unit_of_measure: Optional[str] = Field(default=None, max_length=20)
    unit_price: Optional[Decimal] = Field(default=None, ge=0)
    line_amount: Optional[Decimal] = Field(default=None, ge=0)
    matched_quantity: Optional[Decimal] = Field(default=None, ge=0)


class DeliveryNoteLineResponse(DeliveryNoteLineBase, UUIDMixin, TimestampMixin):
    """Delivery Note Line response schema."""

    model_config = ConfigDict(from_attributes=True)


class DeliveryNoteBase(BaseModel):
    """Delivery Note base schema."""

    dn_number: str = Field(max_length=100)
    supplier_id: str = Field(max_length=100)
    supplier_name: str = Field(max_length=255)
    po_reference: Optional[str] = Field(default=None, max_length=50)
    status: str = Field(default="received")
    currency: str = Field(default="USD", max_length=3)
    total_amount: Decimal = Field(ge=0)
    delivery_date: date
    received_date: date
    notes: Optional[str] = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Delivery Note creation schema."""

    lines: list[DeliveryNoteLineCreate] = Field(default_factory=list)


class DeliveryNoteUpdate(BaseModel):
    """Delivery Note update schema."""

    supplier_id: Optional[str] = Field(default=None, max_length=100)
    supplier_name: Optional[str] = Field(default=None, max_length=255)
    po_reference: Optional[str] = Field(default=None, max_length=50)
    status: Optional[str] = None
    currency: Optional[str] = Field(default=None, max_length=3)
    total_amount: Optional[Decimal] = Field(default=None, ge=0)
    delivery_date: Optional[date] = None
    received_date: Optional[date] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class DeliveryNoteResponse(DeliveryNoteBase, UUIDMixin, TimestampMixin):
    """Delivery Note response schema."""

    model_config = ConfigDict(from_attributes=True)

    is_fully_matched: bool
    is_active: bool
    lines: list[DeliveryNoteLineResponse] = Field(default_factory=list)


class DeliveryNoteListResponse(BaseModel):
    """Delivery Note list response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    dn_number: str
    supplier_id: str
    supplier_name: str
    status: str
    total_amount: Decimal
    delivery_date: date
    is_fully_matched: bool
    created_at: datetime

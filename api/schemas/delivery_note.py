# api/schemas/delivery_note.py
"""Delivery Note schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class DeliveryNoteLineBase(BaseModel):
    """Delivery Note Line base schema."""

    line_number: int = Field(ge=1)
    item_code: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=500)
    quantity: Decimal = Field(ge=0)
    quantity_received: Decimal = Field(default=Decimal("0.0000"), ge=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(ge=0)
    line_amount: Decimal = Field(ge=0)
    tax_rate: Decimal = Field(default=Decimal("0.0000"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    notes: Optional[str] = None


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Delivery Note Line creation schema."""

    pass


class DeliveryNoteLineUpdate(BaseModel):
    """Delivery Note Line update schema."""

    line_number: Optional[int] = Field(default=None, ge=1)
    item_code: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, min_length=1, max_length=500)
    quantity: Optional[Decimal] = Field(default=None, ge=0)
    quantity_received: Optional[Decimal] = Field(default=None, ge=0)
    unit_of_measure: Optional[str] = Field(default=None, max_length=20)
    unit_price: Optional[Decimal] = Field(default=None, ge=0)
    line_amount: Optional[Decimal] = Field(default=None, ge=0)
    tax_rate: Optional[Decimal] = Field(default=None, ge=0)
    tax_amount: Optional[Decimal] = Field(default=None, ge=0)
    notes: Optional[str] = None


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """Delivery Note Line response schema."""

    id: str
    delivery_note_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DeliveryNoteBase(BaseModel):
    """Delivery Note base schema."""

    dn_number: str = Field(min_length=1, max_length=50)
    supplier_id: str = Field(min_length=1, max_length=100)
    supplier_name: str = Field(min_length=1, max_length=255)
    po_reference: Optional[str] = Field(default=None, max_length=50)
    invoice_reference: Optional[str] = Field(default=None, max_length=50)
    delivery_date: date
    received_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    subtotal: Decimal = Field(default=Decimal("0.00"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    total_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    status: str = Field(default="PENDING", max_length=20)
    notes: Optional[str] = None
    metadata_json: Optional[dict[str, Any]] = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Delivery Note creation schema."""

    lines: list[DeliveryNoteLineCreate] = Field(default_factory=list)


class DeliveryNoteUpdate(BaseModel):
    """Delivery Note update schema."""

    dn_number: Optional[str] = Field(default=None, min_length=1, max_length=50)
    supplier_id: Optional[str] = Field(default=None, min_length=1, max_length=100)
    supplier_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    po_reference: Optional[str] = Field(default=None, max_length=50)
    invoice_reference: Optional[str] = Field(default=None, max_length=50)
    delivery_date: Optional[date] = None
    received_date: Optional[date] = None
    currency: Optional[str] = Field(default=None, max_length=3)
    subtotal: Optional[Decimal] = Field(default=None, ge=0)
    tax_amount: Optional[Decimal] = Field(default=None, ge=0)
    total_amount: Optional[Decimal] = Field(default=None, ge=0)
    status: Optional[str] = Field(default=None, max_length=20)
    notes: Optional[str] = None
    metadata_json: Optional[dict[str, Any]] = None


class DeliveryNoteResponse(DeliveryNoteBase):
    """Delivery Note response schema."""

    id: str
    lines: list[DeliveryNoteLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DeliveryNoteListResponse(BaseModel):
    """Delivery Note list response schema."""

    id: str
    dn_number: str
    supplier_id: str
    supplier_name: str
    delivery_date: date
    total_amount: Decimal
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}

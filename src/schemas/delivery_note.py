// src/schemas/delivery_note.py
"""Delivery Note-related Pydantic schemas."""

from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.base import BaseSchema, TimestampMixin
from src.schemas.supplier import SupplierSummary


class DeliveryNoteLineBase(BaseSchema):
    """Base delivery note line schema."""

    line_number: int = Field(ge=1)
    sku: Optional[str] = Field(default=None, max_length=100)
    description: str = Field(min_length=1, max_length=500)
    quantity_ordered: Optional[Decimal] = Field(default=None, decimal_places=3)
    quantity_delivered: Decimal = Field(gt=0, decimal_places=3)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Optional[Decimal] = Field(default=None, ge=0, decimal_places=4)
    line_total: Decimal = Field(ge=0, decimal_places=2)


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating a delivery note line."""

    pass


class DeliveryNoteLineUpdate(BaseSchema):
    """Schema for updating a delivery note line."""

    line_number: Optional[int] = Field(default=None, ge=1)
    sku: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, min_length=1, max_length=500)
    quantity_ordered: Optional[Decimal] = Field(default=None, decimal_places=3)
    quantity_delivered: Optional[Decimal] = Field(default=None, gt=0, decimal_places=3)
    unit_of_measure: Optional[str] = Field(default=None, max_length=20)
    unit_price: Optional[Decimal] = Field(default=None, ge=0, decimal_places=4)
    line_total: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2)


class DeliveryNoteLineResponse(DeliveryNoteLineBase, TimestampMixin):
    """Schema for delivery note line response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    delivery_note_id: UUID


class DeliveryNoteBase(BaseSchema):
    """Base delivery note schema."""

    dn_number: str = Field(min_length=1, max_length=50)
    supplier_id: UUID
    reference_po_number: Optional[str] = Field(default=None, max_length=50)
    delivery_date: date
    received_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    total_amount: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)
    notes: Optional[str] = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating a delivery note."""

    lines: list[DeliveryNoteLineCreate] = Field(default_factory=list)


class DeliveryNoteUpdate(BaseSchema):
    """Schema for updating a delivery note."""

    dn_number: Optional[str] = Field(default=None, min_length=1, max_length=50)
    supplier_id: Optional[UUID] = None
    reference_po_number: Optional[str] = Field(default=None, max_length=50)
    status: Optional[str] = None
    delivery_date: Optional[date] = None
    received_date: Optional[date] = None
    currency: Optional[str] = Field(default=None, max_length=3)
    total_amount: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2)
    notes: Optional[str] = None
    received_by: Optional[UUID] = None


class DeliveryNoteResponse(DeliveryNoteBase, TimestampMixin):
    """Schema for delivery note response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    received_by: Optional[UUID] = None
    supplier: SupplierSummary
    lines: list[DeliveryNoteLineResponse] = Field(default_factory=list)


class DeliveryNoteSummary(BaseSchema):
    """Schema for delivery note summary in nested responses."""

    id: UUID
    dn_number: str
    total_amount: Decimal
    status: str

// src/schemas/delivery_note.py
"""Delivery Note schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.base import BaseSchema, PaginatedResponse


class DeliveryNoteLineBase(BaseModel):
    """Base schema for Delivery Note line items."""

    line_number: int
    sku: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    line_amount: Decimal = Field(..., ge=0)


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating Delivery Note line items."""

    po_line_id: Optional[UUID] = None


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """Schema for Delivery Note line item response."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    delivery_note_id: UUID
    po_line_id: Optional[UUID] = None
    matched_quantity: Decimal
    created_at: datetime
    updated_at: datetime


class DeliveryNoteBase(BaseModel):
    """Base schema for Delivery Notes."""

    dn_number: str = Field(..., max_length=100)
    supplier_id: UUID
    supplier_name: str = Field(..., max_length=255)
    supplier_reference: Optional[str] = Field(None, max_length=100)
    purchase_order_id: Optional[UUID] = None
    delivery_date: date
    received_date: Optional[date] = None
    received_by: Optional[str] = Field(None, max_length=255)
    total_amount: Decimal = Field(..., ge=0)
    total_quantity: Decimal = Field(default=Decimal("0.00"), ge=0)
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating a Delivery Note."""

    lines: list[DeliveryNoteLineCreate] = Field(default_factory=list)


class DeliveryNoteUpdate(BaseModel):
    """Schema for updating a Delivery Note."""

    supplier_name: Optional[str] = Field(None, max_length=255)
    received_by: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    status: Optional[str] = Field(None, max_length=20)
    lines: Optional[list[DeliveryNoteLineCreate]] = None


class DeliveryNoteResponse(DeliveryNoteBase):
    """Schema for Delivery Note response."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    status: str
    matched_amount: Decimal
    unmatched_amount: Decimal
    lines: list[DeliveryNoteLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class DeliveryNoteListResponse(PaginatedResponse[DeliveryNoteResponse]):
    """Paginated list of Delivery Notes."""

    pass

// src/schemas/delivery_note.py
"""Delivery Note schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import ConfigDict, Field

from src.schemas.common import BaseSchema, PaginatedResponse


class DeliveryNoteLineBase(BaseSchema):
    """Base schema for delivery note line items."""

    line_number: int = Field(..., ge=1)
    product_code: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    quantity: Decimal = Field(..., ge=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=0)
    line_total: Decimal = Field(..., ge=0)
    received_quantity: Decimal = Field(default=Decimal("0"), ge=0)
    notes: Optional[str] = None


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating delivery note line items."""

    pass


class DeliveryNoteLineUpdate(BaseSchema):
    """Schema for updating delivery note line items."""

    line_number: Optional[int] = Field(None, ge=1)
    product_code: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    quantity: Optional[Decimal] = Field(None, ge=0)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    line_total: Optional[Decimal] = Field(None, ge=0)
    received_quantity: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """Schema for delivery note line item responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    delivery_note_id: UUID
    created_at: datetime
    updated_at: datetime


class DeliveryNoteBase(BaseSchema):
    """Base schema for Delivery Notes."""

    dn_number: str = Field(..., max_length=50)
    purchase_order_id: Optional[UUID] = None
    supplier_id: UUID
    supplier_name: str = Field(..., max_length=255)
    supplier_code: Optional[str] = Field(None, max_length=50)
    shipment_date: date
    receipt_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    total_amount: Decimal = Field(default=Decimal("0"), ge=0)
    status: str = Field(default="draft", max_length=30)
    notes: Optional[str] = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating Delivery Notes."""

    lines: List[DeliveryNoteLineCreate] = Field(default_factory=list)


class DeliveryNoteUpdate(BaseSchema):
    """Schema for updating Delivery Notes."""

    purchase_order_id: Optional[UUID] = None
    supplier_name: Optional[str] = Field(None, max_length=255)
    supplier_code: Optional[str] = Field(None, max_length=50)
    shipment_date: Optional[date] = None
    receipt_date: Optional[date] = None
    currency: Optional[str] = Field(None, max_length=3)
    total_amount: Optional[Decimal] = Field(None, ge=0)
    status: Optional[str] = Field(None, max_length=30)
    notes: Optional[str] = None


class DeliveryNoteResponse(DeliveryNoteBase):
    """Schema for Delivery Note responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    deleted_at: Optional[datetime] = None
    received_at: Optional[datetime] = None
    lines: List[DeliveryNoteLineResponse] = Field(default_factory=list)


class DeliveryNoteListResponse(PaginatedResponse[DeliveryNoteResponse]):
    """Schema for paginated Delivery Note list response."""

    pass


class DeliveryNoteSummary(BaseSchema):
    """Schema for Delivery Note summary (minimal data)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dn_number: str
    supplier_name: str
    total_amount: Decimal
    status: str
    shipment_date: date

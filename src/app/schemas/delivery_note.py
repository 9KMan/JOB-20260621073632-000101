// src/app/schemas/delivery_note.py
"""Delivery Note schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DeliveryNoteLineBase(BaseModel):
    """Base delivery note line schema."""

    line_number: int = Field(..., ge=1)
    description: str = Field(..., min_length=1, max_length=500)
    sku: Optional[str] = Field(None, max_length=100)
    quantity_delivered: Decimal = Field(..., ge=0)
    quantity_accepted: Decimal = Field(default=Decimal("0"), ge=0)
    quantity_rejected: Decimal = Field(default=Decimal("0"), ge=0)
    unit_price: Decimal = Field(..., ge=0)
    line_total: Decimal = Field(..., ge=0)
    uom: str = Field(default="EA", max_length=20)


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating a DN line."""

    pass


class DeliveryNoteLineUpdate(BaseModel):
    """Schema for updating a DN line."""

    line_number: Optional[int] = Field(None, ge=1)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    sku: Optional[str] = Field(None, max_length=100)
    quantity_delivered: Optional[Decimal] = Field(None, ge=0)
    quantity_accepted: Optional[Decimal] = Field(None, ge=0)
    quantity_rejected: Optional[Decimal] = Field(None, ge=0)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    line_total: Optional[Decimal] = Field(None, ge=0)
    uom: Optional[str] = Field(None, max_length=20)


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """DN line response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    delivery_note_id: UUID
    created_at: datetime
    updated_at: datetime


class DeliveryNoteBase(BaseModel):
    """Base delivery note schema."""

    dn_number: str = Field(..., min_length=1, max_length=100)
    supplier_id: UUID
    purchase_order_id: Optional[UUID] = None
    delivery_date: date
    received_by: Optional[str] = Field(None, max_length=255)
    status: str = Field(default="RECEIVED", max_length=50)
    total_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None
    attachment_url: Optional[str] = Field(None, max_length=500)


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating a delivery note."""

    lines: list[DeliveryNoteLineCreate] = []


class DeliveryNoteUpdate(BaseModel):
    """Schema for updating a delivery note."""

    dn_number: Optional[str] = Field(None, min_length=1, max_length=100)
    supplier_id: Optional[UUID] = None
    purchase_order_id: Optional[UUID] = None
    delivery_date: Optional[date] = None
    received_by: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(None, max_length=50)
    total_amount: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    notes: Optional[str] = None
    attachment_url: Optional[str] = Field(None, max_length=500)
    lines: Optional[list[DeliveryNoteLineCreate]] = None


class DeliveryNoteResponse(DeliveryNoteBase):
    """Delivery note response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class DeliveryNoteDetailResponse(DeliveryNoteResponse):
    """Delivery note detail response with lines."""

    lines: list[DeliveryNoteLineResponse] = []
    supplier_name: Optional[str] = None
    supplier_code: Optional[str] = None
    po_number: Optional[str] = None


class DeliveryNoteListResponse(BaseModel):
    """Schema for DN list response."""

    items: list[DeliveryNoteDetailResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

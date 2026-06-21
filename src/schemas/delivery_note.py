// src/schemas/delivery_note.py
"""Delivery Note schemas."""
import uuid
import decimal
from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict, field_validator

from src.models.enums import DocumentStatus


class DeliveryNoteLineBase(BaseModel):
    """Base schema for Delivery Note line."""
    line_number: int = Field(..., ge=1)
    product_code: Optional[str] = Field(None, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    quantity_delivered: decimal.Decimal = Field(..., ge=0)
    quantity_accepted: Optional[decimal.Decimal] = Field(None, ge=0)
    quantity_rejected: decimal.Decimal = Field(default=decimal.Decimal("0.0000"), ge=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    notes: Optional[str] = Field(None, max_length=500)


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating a Delivery Note line."""
    pass


class DeliveryNoteLineUpdate(BaseModel):
    """Schema for updating a Delivery Note line."""
    product_code: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    quantity_delivered: Optional[decimal.Decimal] = Field(None, ge=0)
    quantity_accepted: Optional[decimal.Decimal] = Field(None, ge=0)
    quantity_rejected: Optional[decimal.Decimal] = Field(None, ge=0)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = Field(None, max_length=500)


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """Schema for Delivery Note line response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    delivery_note_id: uuid.UUID
    is_matched: bool
    matched_quantity: decimal.Decimal
    created_at: datetime
    updated_at: datetime


class DeliveryNoteBase(BaseModel):
    """Base schema for Delivery Note."""
    dn_number: str = Field(..., min_length=1, max_length=100)
    supplier_id: str = Field(..., min_length=1, max_length=100)
    supplier_name: str = Field(..., min_length=1, max_length=255)
    supplier_reference: Optional[str] = Field(None, max_length=100)
    purchase_order_id: Optional[uuid.UUID] = None
    delivery_date: date
    received_by: Optional[str] = Field(None, max_length=255)
    status: DocumentStatus = DocumentStatus.SUBMITTED
    notes: Optional[str] = Field(None, max_length=1000)
    metadata: Optional[str] = Field(None, max_length=2000)


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating a Delivery Note."""
    total_quantity: decimal.Decimal = Field(default=decimal.Decimal("0.0000"), ge=0)
    total_lines: int = Field(default=0, ge=0)
    lines: List[DeliveryNoteLineCreate] = Field(default_factory=list)


class DeliveryNoteUpdate(BaseModel):
    """Schema for updating a Delivery Note."""
    supplier_id: Optional[str] = Field(None, max_length=100)
    supplier_name: Optional[str] = Field(None, max_length=255)
    supplier_reference: Optional[str] = Field(None, max_length=100)
    purchase_order_id: Optional[uuid.UUID] = None
    delivery_date: Optional[date] = None
    received_by: Optional[str] = Field(None, max_length=255)
    total_quantity: Optional[decimal.Decimal] = Field(None, ge=0)
    total_lines: Optional[int] = Field(None, ge=0)
    status: Optional[DocumentStatus] = None
    notes: Optional[str] = Field(None, max_length=1000)
    metadata: Optional[str] = Field(None, max_length=2000)


class DeliveryNoteResponse(DeliveryNoteBase):
    """Schema for Delivery Note response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    total_quantity: decimal.Decimal
    total_lines: int
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    lines: List[DeliveryNoteLineResponse] = Field(default_factory=list)

    @field_validator("lines", mode="before")
    @classmethod
    def validate_lines(cls, v):
        return v if v else []

// src/app/schemas/delivery_note.py
"""Delivery Note schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class DeliveryNoteLineBase(BaseModel):
    """Base schema for delivery note line items."""

    line_number: int = Field(ge=1)
    item_code: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=500)
    quantity: Decimal = Field(gt=0, decimal_places=3)
    delivered_quantity: Decimal = Field(default=Decimal("0.000"), ge=0, decimal_places=3)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(ge=0, decimal_places=2)
    notes: str | None = None

    @field_validator("quantity", "delivered_quantity", mode="before")
    @classmethod
    def validate_quantity(cls, v: Decimal | float | int) -> Decimal:
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return v

    @property
    def line_amount(self) -> Decimal:
        """Calculate line amount."""
        return self.delivered_quantity * self.unit_price


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating delivery note line items."""

    pass


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """Schema for delivery note line item response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dn_id: UUID
    line_amount: Decimal
    created_at: datetime
    updated_at: datetime


class DeliveryNoteBase(BaseModel):
    """Base schema for delivery notes."""

    dn_number: str = Field(min_length=1, max_length=50)
    supplier_id: str = Field(min_length=1, max_length=50)
    supplier_name: str = Field(min_length=1, max_length=255)
    delivery_date: date
    received_by: str | None = Field(default=None, max_length=255)
    currency: str = Field(default="USD", max_length=3)
    notes: str | None = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating a delivery note."""

    lines: list[DeliveryNoteLineCreate] = Field(min_length=1)
    created_by: UUID | None = None

    @model_validator(mode="after")
    def calculate_totals(self) -> Self:
        """Calculate total amounts from lines."""
        subtotal = sum(line.delivered_quantity * line.unit_price for line in self.lines)
        self._subtotal = subtotal
        return self


class DeliveryNoteUpdate(BaseModel):
    """Schema for updating a delivery note."""

    supplier_id: str | None = Field(default=None, max_length=50)
    supplier_name: str | None = Field(default=None, max_length=255)
    received_by: str | None = Field(default=None, max_length=255)
    status: str | None = None
    notes: str | None = None
    lines: list[DeliveryNoteLineCreate] | None = None


class DeliveryNoteResponse(DeliveryNoteBase):
    """Schema for delivery note response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    po_id: UUID | None = None
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    status: str
    created_by: UUID | None = None
    created_at: datetime
    updated_at: datetime
    lines: list[DeliveryNoteLineResponse] = []

    @field_validator("total_amount", "subtotal", "tax_amount", mode="before")
    @classmethod
    def validate_amounts(cls, v: Decimal | None) -> Decimal:
        return v or Decimal("0.00")


class DeliveryNoteListResponse(BaseModel):
    """Schema for paginated delivery note list."""

    items: list[DeliveryNoteResponse]
    total: int
    skip: int
    limit: int


class DeliveryNoteSummary(BaseModel):
    """Schema for delivery note summary in matching."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dn_number: str
    supplier_id: str
    supplier_name: str
    total_amount: Decimal
    status: str

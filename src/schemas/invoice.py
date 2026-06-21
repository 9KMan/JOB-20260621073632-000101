"""Invoice schemas."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field

from src.models.invoice import InvoiceStatus


class InvoiceLineBase(BaseModel):
    line_number: int = Field(ge=1)
    sku: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=512)
    quantity: Decimal = Field(gt=Decimal("0"))
    unit_price: Decimal = Field(ge=Decimal("0"))
    uom: str = Field(default="EA", min_length=1, max_length=16)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def line_total(self) -> Decimal:
        return (self.quantity * self.unit_price).quantize(Decimal("0.0001"))


class InvoiceLineCreate(InvoiceLineBase):
    """Create payload — ``line_total`` is derived from quantity × unit_price."""


class InvoiceLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    line_number: int
    sku: str
    description: str | None
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal
    uom: str
    created_at: datetime
    updated_at: datetime


class InvoiceBase(BaseModel):
    invoice_number: str = Field(min_length=1, max_length=64)
    supplier_id: UUID
    invoice_date: date
    due_date: date | None = None
    po_number: str | None = Field(default=None, max_length=64)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    tax_amount: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))


class InvoiceCreate(InvoiceBase):
    lines: list[InvoiceLineCreate] = Field(min_length=1)


class InvoiceRead(InvoiceBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: InvoiceStatus
    total_amount: Decimal
    created_at: datetime
    updated_at: datetime
    lines: list[InvoiceLineRead] = Field(default_factory=list)

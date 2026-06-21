"""Purchase order schemas."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field

from src.models.purchase_order import PurchaseOrderStatus


class PurchaseOrderLineBase(BaseModel):
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


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Create payload — ``line_total`` is derived from quantity × unit_price."""


class PurchaseOrderLineRead(BaseModel):
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


class PurchaseOrderBase(BaseModel):
    po_number: str = Field(min_length=1, max_length=64)
    supplier_id: UUID
    order_date: date
    expected_delivery_date: date | None = None
    currency: str = Field(default="USD", min_length=3, max_length=3)


class PurchaseOrderCreate(PurchaseOrderBase):
    lines: list[PurchaseOrderLineCreate] = Field(min_length=1)


class PurchaseOrderRead(PurchaseOrderBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: PurchaseOrderStatus
    total_amount: Decimal
    created_at: datetime
    updated_at: datetime
    lines: list[PurchaseOrderLineRead] = Field(default_factory=list)

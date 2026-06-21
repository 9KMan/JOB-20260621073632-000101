// src/app/schemas/purchase_order.py
"""Purchase Order schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class PurchaseOrderLineBase(BaseModel):
    """Base schema for PO line items."""

    line_number: int = Field(ge=1)
    item_code: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=500)
    quantity: Decimal = Field(gt=0, decimal_places=3)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(ge=0, decimal_places=2)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)
    expected_delivery_date: date | None = None
    notes: str | None = None

    @field_validator("quantity", mode="before")
    @classmethod
    def validate_quantity(cls, v: Decimal | float | int) -> Decimal:
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return v

    @property
    def line_amount(self) -> Decimal:
        """Calculate line amount."""
        return (self.quantity * self.unit_price) + self.tax_amount


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Schema for creating PO line items."""

    pass


class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    """Schema for PO line item response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    po_id: UUID
    line_amount: Decimal
    created_at: datetime
    updated_at: datetime


class PurchaseOrderBase(BaseModel):
    """Base schema for purchase orders."""

    po_number: str = Field(min_length=1, max_length=50)
    supplier_id: str = Field(min_length=1, max_length=50)
    supplier_name: str = Field(min_length=1, max_length=255)
    order_date: date
    expected_delivery_date: date | None = None
    currency: str = Field(default="USD", max_length=3)
    notes: str | None = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a purchase order."""

    lines: list[PurchaseOrderLineCreate] = Field(min_length=1)
    created_by: UUID | None = None

    @model_validator(mode="after")
    def calculate_totals(self) -> Self:
        """Calculate total amounts from lines."""
        subtotal = sum(line.quantity * line.unit_price for line in self.lines)
        tax_total = sum(line.tax_amount for line in self.lines)
        self._subtotal = subtotal
        self._tax_total = tax_total
        return self


class PurchaseOrderUpdate(BaseModel):
    """Schema for updating a purchase order."""

    supplier_id: str | None = Field(default=None, max_length=50)
    supplier_name: str | None = Field(default=None, max_length=255)
    expected_delivery_date: date | None = None
    status: str | None = None
    notes: str | None = None
    lines: list[PurchaseOrderLineCreate] | None = None


class PurchaseOrderResponse(PurchaseOrderBase):
    """Schema for purchase order response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    total_amount: Decimal
    status: str
    created_by: UUID | None = None
    created_at: datetime
    updated_at: datetime
    lines: list[PurchaseOrderLineResponse] = []

    @field_validator("total_amount", mode="before")
    @classmethod
    def validate_total(cls, v: Decimal | None) -> Decimal:
        return v or Decimal("0.00")


class PurchaseOrderListResponse(BaseModel):
    """Schema for paginated PO list."""

    items: list[PurchaseOrderResponse]
    total: int
    skip: int
    limit: int


class PurchaseOrderSummary(BaseModel):
    """Schema for PO summary in matching."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    po_number: str
    supplier_id: str
    supplier_name: str
    total_amount: Decimal
    open_amount: Decimal
    status: str

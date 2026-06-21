// src/schemas/purchase_order.py
"""Purchase Order-related Pydantic schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.base import BaseSchema, TimestampMixin
from src.schemas.supplier import SupplierSummary


class PurchaseOrderLineBase(BaseSchema):
    """Base purchase order line schema."""

    line_number: int = Field(ge=1)
    sku: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=500)
    quantity: Decimal = Field(gt=0, decimal_places=3)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(gt=0, decimal_places=4)
    line_total: Decimal = Field(gt=0, decimal_places=2)
    tax_rate: Decimal = Field(default=Decimal("0.0000"), ge=0, decimal_places=4)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)
    delivery_date: Optional[date] = None


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Schema for creating a purchase order line."""

    pass


class PurchaseOrderLineUpdate(BaseSchema):
    """Schema for updating a purchase order line."""

    line_number: Optional[int] = Field(default=None, ge=1)
    sku: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, min_length=1, max_length=500)
    quantity: Optional[Decimal] = Field(default=None, gt=0, decimal_places=3)
    unit_of_measure: Optional[str] = Field(default=None, max_length=20)
    unit_price: Optional[Decimal] = Field(default=None, gt=0, decimal_places=4)
    line_total: Optional[Decimal] = Field(default=None, gt=0, decimal_places=2)
    tax_rate: Optional[Decimal] = Field(default=None, ge=0, decimal_places=4)
    tax_amount: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2)
    delivery_date: Optional[date] = None


class PurchaseOrderLineResponse(PurchaseOrderLineBase, TimestampMixin):
    """Schema for purchase order line response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    purchase_order_id: UUID


class PurchaseOrderBase(BaseSchema):
    """Base purchase order schema."""

    po_number: str = Field(min_length=1, max_length=50)
    supplier_id: UUID
    po_date: date
    expected_delivery_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    subtotal: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)
    total_amount: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)
    notes: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a purchase order."""

    lines: list[PurchaseOrderLineCreate] = Field(default_factory=list)


class PurchaseOrderUpdate(BaseSchema):
    """Schema for updating a purchase order."""

    po_number: Optional[str] = Field(default=None, min_length=1, max_length=50)
    supplier_id: Optional[UUID] = None
    status: Optional[str] = None
    po_date: Optional[date] = None
    expected_delivery_date: Optional[date] = None
    currency: Optional[str] = Field(default=None, max_length=3)
    subtotal: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2)
    tax_amount: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2)
    total_amount: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2)
    notes: Optional[str] = None
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None


class PurchaseOrderResponse(PurchaseOrderBase, TimestampMixin):
    """Schema for purchase order response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    supplier: SupplierSummary
    lines: list[PurchaseOrderLineResponse] = Field(default_factory=list)


class PurchaseOrderSummary(BaseSchema):
    """Schema for purchase order summary in nested responses."""

    id: UUID
    po_number: str
    total_amount: Decimal
    status: str

// src/app/schemas/purchase_order.py
"""Purchase Order schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import BaseSchema, TimestampMixin, UUIDMixin


class POLineBase(BaseModel):
    """PO Line base schema."""

    line_number: int = Field(ge=1)
    product_code: str = Field(max_length=100)
    product_description: str = Field(max_length=500)
    quantity: Decimal = Field(ge=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(ge=0)
    line_amount: Decimal = Field(ge=0)
    tax_rate: Decimal = Field(default=Decimal("0.00"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    expected_quantity: Decimal = Field(ge=0)
    delivered_quantity: Decimal = Field(default=Decimal("0.00"), ge=0)


class POLineCreate(POLineBase):
    """PO Line creation schema."""

    pass


class POLineUpdate(BaseModel):
    """PO Line update schema."""

    product_code: Optional[str] = Field(default=None, max_length=100)
    product_description: Optional[str] = Field(default=None, max_length=500)
    quantity: Optional[Decimal] = Field(default=None, ge=0)
    unit_of_measure: Optional[str] = Field(default=None, max_length=20)
    unit_price: Optional[Decimal] = Field(default=None, ge=0)
    line_amount: Optional[Decimal] = Field(default=None, ge=0)
    tax_rate: Optional[Decimal] = Field(default=None, ge=0)
    tax_amount: Optional[Decimal] = Field(default=None, ge=0)
    expected_quantity: Optional[Decimal] = Field(default=None, ge=0)
    delivered_quantity: Optional[Decimal] = Field(default=None, ge=0)


class POLineResponse(POLineBase, UUIDMixin, TimestampMixin):
    """PO Line response schema."""

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderBase(BaseModel):
    """Purchase Order base schema."""

    po_number: str = Field(max_length=50)
    supplier_id: str = Field(max_length=100)
    supplier_name: str = Field(max_length=255)
    supplier_reference: Optional[str] = Field(default=None, max_length=100)
    status: str = Field(default="draft")
    currency: str = Field(default="USD", max_length=3)
    total_amount: Decimal = Field(ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    po_date: date
    expected_delivery_date: Optional[date] = None
    notes: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Purchase Order creation schema."""

    lines: list[POLineCreate] = Field(default_factory=list)


class PurchaseOrderUpdate(BaseModel):
    """Purchase Order update schema."""

    supplier_id: Optional[str] = Field(default=None, max_length=100)
    supplier_name: Optional[str] = Field(default=None, max_length=255)
    supplier_reference: Optional[str] = Field(default=None, max_length=100)
    status: Optional[str] = None
    currency: Optional[str] = Field(default=None, max_length=3)
    total_amount: Optional[Decimal] = Field(default=None, ge=0)
    tax_amount: Optional[Decimal] = Field(default=None, ge=0)
    po_date: Optional[date] = None
    expected_delivery_date: Optional[date] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class PurchaseOrderResponse(PurchaseOrderBase, UUIDMixin, TimestampMixin):
    """Purchase Order response schema."""

    model_config = ConfigDict(from_attributes=True)

    is_fully_matched: bool
    is_active: bool
    lines: list[POLineResponse] = Field(default_factory=list)


class PurchaseOrderListResponse(BaseModel):
    """Purchase Order list response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    po_number: str
    supplier_id: str
    supplier_name: str
    status: str
    total_amount: Decimal
    po_date: date
    is_fully_matched: bool
    created_at: datetime

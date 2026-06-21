# api/schemas/purchase_order.py
"""Purchase Order schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class PurchaseOrderLineBase(BaseModel):
    """Purchase Order Line base schema."""

    line_number: int = Field(ge=1)
    item_code: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=500)
    quantity: Decimal = Field(ge=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(ge=0)
    line_amount: Decimal = Field(ge=0)
    tax_rate: Decimal = Field(default=Decimal("0.0000"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    expected_delivery_date: Optional[date] = None
    notes: Optional[str] = None


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Purchase Order Line creation schema."""

    pass


class PurchaseOrderLineUpdate(BaseModel):
    """Purchase Order Line update schema."""

    line_number: Optional[int] = Field(default=None, ge=1)
    item_code: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, min_length=1, max_length=500)
    quantity: Optional[Decimal] = Field(default=None, ge=0)
    unit_of_measure: Optional[str] = Field(default=None, max_length=20)
    unit_price: Optional[Decimal] = Field(default=None, ge=0)
    line_amount: Optional[Decimal] = Field(default=None, ge=0)
    tax_rate: Optional[Decimal] = Field(default=None, ge=0)
    tax_amount: Optional[Decimal] = Field(default=None, ge=0)
    expected_delivery_date: Optional[date] = None
    notes: Optional[str] = None


class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    """Purchase Order Line response schema."""

    id: str
    purchase_order_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PurchaseOrderBase(BaseModel):
    """Purchase Order base schema."""

    po_number: str = Field(min_length=1, max_length=50)
    supplier_id: str = Field(min_length=1, max_length=100)
    supplier_name: str = Field(min_length=1, max_length=255)
    order_date: date
    expected_delivery_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    subtotal: Decimal = Field(default=Decimal("0.00"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    total_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    status: str = Field(default="OPEN", max_length=20)
    notes: Optional[str] = None
    metadata_json: Optional[dict[str, Any]] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Purchase Order creation schema."""

    lines: list[PurchaseOrderLineCreate] = Field(default_factory=list)


class PurchaseOrderUpdate(BaseModel):
    """Purchase Order update schema."""

    po_number: Optional[str] = Field(default=None, min_length=1, max_length=50)
    supplier_id: Optional[str] = Field(default=None, min_length=1, max_length=100)
    supplier_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    order_date: Optional[date] = None
    expected_delivery_date: Optional[date] = None
    currency: Optional[str] = Field(default=None, max_length=3)
    subtotal: Optional[Decimal] = Field(default=None, ge=0)
    tax_amount: Optional[Decimal] = Field(default=None, ge=0)
    total_amount: Optional[Decimal] = Field(default=None, ge=0)
    status: Optional[str] = Field(default=None, max_length=20)
    notes: Optional[str] = None
    metadata_json: Optional[dict[str, Any]] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    """Purchase Order response schema."""

    id: str
    lines: list[PurchaseOrderLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PurchaseOrderListResponse(BaseModel):
    """Purchase Order list response schema."""

    id: str
    po_number: str
    supplier_id: str
    supplier_name: str
    order_date: date
    total_amount: Decimal
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}

# src/schemas/purchase_order.py
"""Purchase Order schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PurchaseOrderLineBase(BaseModel):
    """Base purchase order line schema."""
    line_number: int
    item_code: str
    item_description: str
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    line_amount: Decimal = Field(ge=0)
    uom: Optional[str] = None


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Purchase order line creation schema."""
    pass


class PurchaseOrderLineUpdate(BaseModel):
    """Purchase order line update schema."""
    line_number: Optional[int] = None
    item_code: Optional[str] = None
    item_description: Optional[str] = None
    quantity: Optional[Decimal] = Field(default=None, gt=0)
    unit_price: Optional[Decimal] = Field(default=None, ge=0)
    line_amount: Optional[Decimal] = Field(default=None, ge=0)
    uom: Optional[str] = None


class PurchaseOrderLineInDB(PurchaseOrderLineBase):
    """Purchase order line database schema."""
    id: UUID
    purchase_order_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    """Purchase order line response schema."""
    id: UUID
    purchase_order_id: UUID

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderBase(BaseModel):
    """Base purchase order schema."""
    po_number: str = Field(max_length=100)
    supplier_id: str = Field(max_length=100)
    supplier_name: str = Field(max_length=255)
    po_date: date
    expected_delivery_date: Optional[date] = None
    total_amount: Decimal = Field(gt=0)
    currency: str = Field(default="USD", max_length=3)
    status: str = Field(default="open", max_length=50)
    notes: Optional[str] = Field(default=None, max_length=1000)


class PurchaseOrderCreate(PurchaseOrderBase):
    """Purchase order creation schema."""
    line_items: List[PurchaseOrderLineCreate] = []


class PurchaseOrderUpdate(BaseModel):
    """Purchase order update schema."""
    po_number: Optional[str] = Field(default=None, max_length=100)
    supplier_id: Optional[str] = Field(default=None, max_length=100)
    supplier_name: Optional[str] = Field(default=None, max_length=255)
    po_date: Optional[date] = None
    expected_delivery_date: Optional[date] = None
    total_amount: Optional[Decimal] = Field(default=None, gt=0)
    currency: Optional[str] = Field(default=None, max_length=3)
    status: Optional[str] = Field(default=None, max_length=50)
    notes: Optional[str] = Field(default=None, max_length=1000)
    line_items: Optional[List[PurchaseOrderLineCreate]] = None


class PurchaseOrderInDB(PurchaseOrderBase):
    """Purchase order database schema."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderResponse(PurchaseOrderBase):
    """Purchase order response schema."""
    id: UUID
    line_items: List[PurchaseOrderLineResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderListResponse(BaseModel):
    """Purchase order list response schema."""
    items: List[PurchaseOrderResponse]
    total: int
    page: int
    page_size: int

# app/schemas/purchase_order.py
"""Purchase Order schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class PurchaseOrderLineBase(BaseModel):
    """Base purchase order line schema."""

    line_number: int = Field(..., ge=1)
    product_code: Optional[str] = Field(None, max_length=100)
    description: str = Field(..., min_length=1)
    quantity: Decimal = Field(..., ge=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=0)
    tax_rate: Decimal = Field(default=Decimal("0"), ge=0, le=1)
    expected_delivery_date: Optional[str] = None


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Purchase order line creation request."""

    pass


class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    """Purchase order line response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    line_total: Decimal
    created_at: datetime
    updated_at: datetime


class PurchaseOrderBase(BaseModel):
    """Base purchase order schema."""

    po_number: str = Field(..., min_length=1, max_length=50)
    vendor_id: str
    order_date: str
    expected_delivery_date: Optional[str] = None
    currency: str = Field(default="USD", max_length=3)
    shipping_cost: Decimal = Field(default=Decimal("0"), ge=0)
    notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Purchase order creation request."""

    lines: List[PurchaseOrderLineCreate]
    status: str = Field(default="submitted")


class PurchaseOrderUpdate(BaseModel):
    """Purchase order update request."""

    po_number: Optional[str] = Field(None, min_length=1, max_length=50)
    vendor_id: Optional[str] = None
    status: Optional[str] = None
    order_date: Optional[str] = None
    expected_delivery_date: Optional[str] = None
    currency: Optional[str] = Field(None, max_length=3)
    shipping_cost: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    """Purchase order response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    lines: List[PurchaseOrderLineResponse] = []


class PurchaseOrderListResponse(BaseModel):
    """Purchase order list response with pagination."""

    items: List[PurchaseOrderResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

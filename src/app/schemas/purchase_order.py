// src/app/schemas/purchase_order.py
"""Purchase Order Pydantic schemas."""

from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field

from src.app.schemas.supplier import SupplierResponse


class PurchaseOrderLineBase(BaseModel):
    """Base purchase order line schema."""

    line_number: int = Field(..., ge=1)
    item_code: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    line_total: Decimal = Field(..., ge=0)
    uom: Optional[str] = Field(None, max_length=20)


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Schema for creating a purchase order line."""

    pass


class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    """Schema for purchase order line response."""

    id: str
    purchase_order_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PurchaseOrderBase(BaseModel):
    """Base purchase order schema."""

    po_number: str = Field(..., min_length=1, max_length=50)
    supplier_id: str
    order_date: date
    expected_delivery_date: Optional[date] = None
    total_amount: Decimal = Field(..., ge=0)
    currency: str = Field(default="USD", max_length=3)
    status: str = Field(default="OPEN", max_length=20)
    notes: Optional[str] = Field(None, max_length=1000)


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a purchase order."""

    lines: List[PurchaseOrderLineCreate] = Field(..., min_length=1)


class PurchaseOrderUpdate(BaseModel):
    """Schema for updating a purchase order."""

    expected_delivery_date: Optional[date] = None
    status: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = Field(None, max_length=1000)


class PurchaseOrderResponse(PurchaseOrderBase):
    """Schema for purchase order response."""

    id: str
    created_at: datetime
    updated_at: datetime
    lines: List[PurchaseOrderLineResponse] = []
    supplier: Optional[SupplierResponse] = None

    class Config:
        from_attributes = True


class PurchaseOrderListResponse(BaseModel):
    """Schema for paginated purchase order list response."""

    items: List[PurchaseOrderResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

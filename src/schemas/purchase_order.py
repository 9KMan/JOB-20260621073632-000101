// src/schemas/purchase_order.py
"""Purchase Order schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PurchaseOrderLineItemBase(BaseModel):
    """Base line item schema."""
    line_number: int = Field(..., ge=1)
    item_code: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=0)
    tax_rate: Decimal = Field(default=Decimal("0.0000"), ge=0)
    line_total: Decimal = Field(..., ge=0)


class PurchaseOrderLineItemCreate(PurchaseOrderLineItemBase):
    """Schema for line item creation."""
    pass


class PurchaseOrderLineItemResponse(PurchaseOrderLineItemBase):
    """Schema for line item response."""
    id: UUID
    purchase_order_id: UUID
    
    model_config = {"from_attributes": True}


class PurchaseOrderBase(BaseModel):
    """Base purchase order schema."""
    po_number: str = Field(..., max_length=50)
    supplier_id: UUID
    order_date: date
    expected_delivery_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for purchase order creation."""
    line_items: list[PurchaseOrderLineItemCreate] = Field(default_factory=list)


class PurchaseOrderUpdate(BaseModel):
    """Schema for purchase order update."""
    po_number: Optional[str] = Field(None, max_length=50)
    supplier_id: Optional[UUID] = None
    order_date: Optional[date] = None
    expected_delivery_date: Optional[date] = None
    status: Optional[str] = Field(None, max_length=20)
    currency: Optional[str] = Field(None, max_length=3)
    notes: Optional[str] = None
    line_items: Optional[list[PurchaseOrderLineItemCreate]] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    """Schema for purchase order response."""
    id: UUID
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    line_items: list[PurchaseOrderLineItemResponse] = []
    
    model_config = {"from_attributes": True}


class PurchaseOrderListResponse(BaseModel):
    """Schema for paginated purchase order list."""
    items: list[PurchaseOrderResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

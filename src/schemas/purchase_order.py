# src/schemas/purchase_order.py
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field

from src.schemas.common import TimestampMixinSchema, UUIDMixinSchema


# Line Items
class PurchaseOrderLineItemBase(BaseModel):
    """Base schema for PO line items."""
    line_number: int = Field(ge=1)
    item_code: str = Field(max_length=100)
    description: str = Field(max_length=500)
    quantity: Decimal = Field(ge=0)
    unit_price: Decimal = Field(ge=0)
    line_total: Decimal = Field(ge=0)


class PurchaseOrderLineItemCreate(PurchaseOrderLineItemBase):
    """Schema for creating PO line items."""
    pass


class PurchaseOrderLineItemResponse(PurchaseOrderLineItemBase, UUIDMixinSchema):
    """Schema for PO line item response."""
    purchase_order_id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


# Purchase Order
class PurchaseOrderBase(BaseModel):
    """Base schema for Purchase Orders."""
    po_number: str = Field(max_length=50)
    supplier_id: str = Field(max_length=100)
    supplier_name: str = Field(max_length=255)
    order_date: date
    expected_delivery_date: Optional[date] = None
    subtotal: Decimal = Field(ge=0)
    tax_amount: Decimal = Field(ge=0, default=Decimal("0.00"))
    total_amount: Decimal = Field(ge=0)
    currency: str = Field(default="USD", max_length=3)
    status: str = Field(default="OPEN", max_length=20)
    notes: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating Purchase Orders."""
    line_items: List[PurchaseOrderLineItemCreate] = []


class PurchaseOrderUpdate(BaseModel):
    """Schema for updating Purchase Orders."""
    supplier_name: Optional[str] = None
    expected_delivery_date: Optional[date] = None
    subtotal: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class PurchaseOrderResponse(PurchaseOrderBase, UUIDMixinSchema, TimestampMixinSchema):
    """Schema for Purchase Order response."""
    line_items: List[PurchaseOrderLineItemResponse] = []
    
    model_config = {"from_attributes": True}

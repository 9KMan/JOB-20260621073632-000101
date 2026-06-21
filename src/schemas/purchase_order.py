// src/schemas/purchase_order.py
"""Purchase order schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.models.purchase_order import POStatus
from src.schemas.common import BaseSchema, TimestampSchema


class PurchaseOrderLineBase(BaseSchema):
    """Base PO line schema."""
    line_number: int
    sku: Optional[str] = None
    description: str = Field(max_length=500)
    quantity: Decimal = Field(gt=0)
    unit_of_measure: str = "EA"
    unit_price: Decimal = Field(ge=0)
    tax_rate: Decimal = Field(default=Decimal("0.00"), ge=0)
    received_quantity: Decimal = Field(default=Decimal("0.00"), ge=0)
    invoiced_quantity: Decimal = Field(default=Decimal("0.00"), ge=0)


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """PO line creation schema."""
    pass


class PurchaseOrderLineResponse(PurchaseOrderLineBase, TimestampSchema):
    """PO line response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    purchase_order_id: UUID
    line_total: Decimal


class PurchaseOrderBase(BaseSchema):
    """Base purchase order schema."""
    po_number: str = Field(max_length=50)
    supplier_id: str = Field(max_length=100)
    supplier_name: str = Field(max_length=255)
    supplier_reference: Optional[str] = None
    order_date: str
    expected_delivery_date: Optional[str] = None
    currency: str = "USD"
    notes: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Purchase order creation schema."""
    lines: list[PurchaseOrderLineCreate]


class PurchaseOrderUpdate(BaseSchema):
    """Purchase order update schema."""
    supplier_name: Optional[str] = None
    supplier_reference: Optional[str] = None
    expected_delivery_date: Optional[str] = None
    status: Optional[POStatus] = None
    notes: Optional[str] = None
    lines: Optional[list[PurchaseOrderLineCreate]] = None


class PurchaseOrderResponse(PurchaseOrderBase, TimestampSchema):
    """Purchase order response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    status: POStatus
    lines: list[PurchaseOrderLineResponse] = []

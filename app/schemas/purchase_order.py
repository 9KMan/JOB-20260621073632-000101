// app/schemas/purchase_order.py
"""Purchase Order schemas."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field


class PurchaseOrderLineBase(BaseModel):
    """Base purchase order line schema."""
    line_number: int = Field(..., ge=1)
    product_code: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=0)
    tax_rate: Decimal = Field(default=Decimal("0.0000"), ge=0, le=1)
    line_total: Decimal = Field(..., ge=0)


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Schema for creating a purchase order line."""
    pass


class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    """Schema for purchase order line response."""
    id: uuid.UUID
    purchase_order_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class PurchaseOrderBase(BaseModel):
    """Base purchase order schema."""
    po_number: str = Field(..., min_length=1, max_length=50)
    vendor_id: uuid.UUID
    order_date: date
    expected_delivery_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a purchase order."""
    status: str = Field(default="DRAFT", max_length=20)
    lines: List[PurchaseOrderLineCreate] = Field(default_factory=list)


class PurchaseOrderUpdate(BaseModel):
    """Schema for updating a purchase order."""
    vendor_id: Optional[uuid.UUID] = None
    order_date: Optional[date] = None
    expected_delivery_date: Optional[date] = None
    status: Optional[str] = Field(None, max_length=20)
    currency: Optional[str] = Field(None, max_length=3)
    notes: Optional[str] = None
    lines: Optional[List[PurchaseOrderLineCreate]] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    """Schema for purchase order response."""
    id: uuid.UUID
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    created_at: datetime
    updated_at: datetime
    lines: List[PurchaseOrderLineResponse] = []
    
    model_config = {"from_attributes": True}

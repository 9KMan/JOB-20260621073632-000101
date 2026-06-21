// src/app/schemas/purchase_order.py
"""Purchase Order Pydantic schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class PurchaseOrderLineBase(BaseModel):
    """Base purchase order line schema."""
    line_number: int = Field(..., ge=1)
    item_code: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., min_length=1, max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=0)
    tax_rate: Decimal = Field(default=Decimal("0.00"), ge=0)


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Purchase order line creation schema."""
    pass


class PurchaseOrderLineUpdate(BaseModel):
    """Purchase order line update schema."""
    item_code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    tax_rate: Optional[Decimal] = Field(None, ge=0)


class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    """Purchase order line response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    purchase_order_id: UUID
    line_amount: Decimal
    tax_amount: Decimal
    matched_quantity: Decimal
    open_quantity: Decimal
    created_at: datetime
    updated_at: datetime


class PurchaseOrderBase(BaseModel):
    """Base purchase order schema."""
    po_number: str = Field(..., min_length=1, max_length=50)
    supplier_id: UUID
    supplier_name: str = Field(..., min_length=1, max_length=255)
    po_date: date
    expected_delivery_date: Optional[date] = None
    payment_terms: Optional[str] = Field(None, max_length=100)
    shipping_address: Optional[str] = None
    notes: Optional[str] = None
    currency: str = Field(default="USD", max_length=3)


class PurchaseOrderCreate(PurchaseOrderBase):
    """Purchase order creation schema."""
    lines: List[PurchaseOrderLineCreate] = Field(..., min_length=1)
    status: str = Field(default="open", max_length=20)


class PurchaseOrderUpdate(BaseModel):
    """Purchase order update schema."""
    supplier_name: Optional[str] = Field(None, max_length=255)
    po_date: Optional[date] = None
    expected_delivery_date: Optional[date] = None
    payment_terms: Optional[str] = Field(None, max_length=100)
    shipping_address: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = Field(None, max_length=20)


class PurchaseOrderResponse(PurchaseOrderBase):
    """Purchase order response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    status: str
    total_amount: Decimal
    matched_amount: Decimal
    open_amount: Decimal
    lines: List[PurchaseOrderLineResponse] = []
    created_at: datetime
    updated_at: datetime

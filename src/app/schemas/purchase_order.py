// src/app/schemas/purchase_order.py
"""Purchase Order schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PurchaseOrderLineBase(BaseModel):
    """Base purchase order line schema."""
    
    line_number: int = Field(ge=1)
    product_code: str = Field(max_length=100)
    product_name: str = Field(max_length=255)
    description: Optional[str] = None
    quantity: Decimal = Field(ge=0, decimal_places=3)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(ge=0, decimal_places=4)
    tax_code: Optional[str] = None
    tax_rate: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    expected_delivery_date: Optional[date] = None
    notes: Optional[str] = None


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Purchase order line creation schema."""
    pass


class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    """Purchase order line response schema."""
    
    id: str
    purchase_order_id: str
    line_amount: Decimal
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderBase(BaseModel):
    """Base purchase order schema."""
    
    po_number: str = Field(max_length=50)
    supplier_id: str
    supplier_name: str = Field(max_length=255)
    supplier_code: str = Field(max_length=50)
    order_date: date
    expected_delivery_date: Optional[date] = None
    delivery_address: Optional[str] = None
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Purchase order creation schema."""
    
    lines: list[PurchaseOrderLineCreate] = Field(min_length=1)
    status: Optional[str] = "draft"


class PurchaseOrderUpdate(BaseModel):
    """Purchase order update schema."""
    
    supplier_name: Optional[str] = None
    supplier_code: Optional[str] = None
    expected_delivery_date: Optional[date] = None
    delivery_address: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    """Purchase order response schema."""
    
    id: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    status: str
    is_archived: bool
    lines: list[PurchaseOrderLineResponse] = []
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderListResponse(BaseModel):
    """Purchase order list response with pagination."""
    
    purchase_orders: list[PurchaseOrderResponse]
    total: int
    page: int
    page_size: int


class PurchaseOrderSummary(BaseModel):
    """Purchase order summary for matching."""
    
    id: str
    po_number: str
    supplier_code: str
    total_amount: Decimal
    currency: str
    status: str
    open_amount: Decimal
    line_count: int
    
    model_config = ConfigDict(from_attributes=True)

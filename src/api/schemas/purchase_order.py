// src/api/schemas/purchase_order.py
from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from src.models.purchase_order import POStatus


class PurchaseOrderLineBase(BaseModel):
    """Base PO line schema."""
    line_number: int
    item_code: Optional[str] = None
    description: str = Field(..., max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_of_measure: str = "EA"
    unit_price: Decimal = Field(..., ge=0)
    tax_rate: Decimal = Field(default=Decimal("0"), ge=0, le=1)
    expected_delivery_date: Optional[date] = None
    notes: Optional[str] = None


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """PO line creation schema."""
    pass


class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    """PO line response schema."""
    id: UUID
    line_total: Decimal
    tax_amount: Decimal
    
    class Config:
        from_attributes = True


class PurchaseOrderBase(BaseModel):
    """Base PO schema."""
    po_number: str = Field(..., max_length=100)
    supplier_id: UUID
    supplier_name: str = Field(..., max_length=255)
    supplier_code: Optional[str] = None
    order_date: date
    expected_delivery_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """PO creation schema."""
    line_items: List[PurchaseOrderLineCreate] = Field(default_factory=list)


class PurchaseOrderUpdate(BaseModel):
    """PO update schema."""
    supplier_name: Optional[str] = None
    supplier_code: Optional[str] = None
    expected_delivery_date: Optional[date] = None
    status: Optional[POStatus] = None
    notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    """PO response schema."""
    id: UUID
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    status: POStatus
    created_at: datetime
    updated_at: datetime
    line_items: List[PurchaseOrderLineResponse] = []
    
    class Config:
        from_attributes = True


class PurchaseOrderListResponse(BaseModel):
    """PO list response schema."""
    items: List[PurchaseOrderResponse]
    total: int
    page: int
    page_size: int

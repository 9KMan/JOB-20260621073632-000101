// src/api/schemas/purchase_order.py
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from datetime import date
from src.models.purchase_order import POStatus


class PurchaseOrderLineBase(BaseModel):
    line_number: int
    product_code: str
    description: str
    quantity: Decimal
    unit_of_measure: str = "EA"
    unit_price: Decimal


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    pass


class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    id: UUID
    line_total: Decimal
    
    class Config:
        from_attributes = True


class PurchaseOrderBase(BaseModel):
    po_number: str
    supplier_code: str
    supplier_name: str
    order_date: date
    expected_delivery_date: Optional[date] = None
    currency: str = "USD"
    notes: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    lines: List[PurchaseOrderLineCreate]


class PurchaseOrderUpdate(BaseModel):
    supplier_code: Optional[str] = None
    supplier_name: Optional[str] = None
    status: Optional[POStatus] = None
    expected_delivery_date: Optional[date] = None
    notes: Optional[str] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    id: UUID
    status: POStatus
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    created_at: date
    updated_at: date
    lines: List[PurchaseOrderLineResponse] = []
    
    class Config:
        from_attributes = True

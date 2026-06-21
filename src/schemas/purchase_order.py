// src/schemas/purchase_order.py
"""
Purchase Order Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal

from src.schemas.common import TimestampMixin, UUIDMixin


class PurchaseOrderLineBase(BaseModel):
    """Base schema for PO line items"""
    line_number: int
    item_code: Optional[str] = None
    description: str = Field(..., max_length=500)
    quantity: Decimal = Field(..., ge=0)
    unit_of_measure: str = "EA"
    unit_price: Decimal = Field(..., ge=0)
    tax_rate: Decimal = Field(default=Decimal("0"), ge=0)


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Schema for creating PO line items"""
    pass


class PurchaseOrderLineResponse(PurchaseOrderLineBase, UUIDMixin):
    """Response schema for PO line items"""
    line_amount: Decimal
    tax_amount: Decimal
    
    class Config:
        from_attributes = True


class PurchaseOrderBase(BaseModel):
    """Base schema for Purchase Order"""
    po_number: str = Field(..., max_length=50)
    supplier_id: UUID
    supplier_name: str = Field(..., max_length=255)
    supplier_code: Optional[str] = None
    po_date: datetime
    expected_delivery_date: Optional[datetime] = None
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a Purchase Order"""
    line_items: List[PurchaseOrderLineCreate] = Field(default_factory=list)


class PurchaseOrderUpdate(BaseModel):
    """Schema for updating a Purchase Order"""
    supplier_name: Optional[str] = None
    supplier_code: Optional[str] = None
    expected_delivery_date: Optional[datetime] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None


class PurchaseOrderResponse(PurchaseOrderBase, UUIDMixin, TimestampMixin):
    """Response schema for Purchase Order"""
    total_amount: Decimal
    status: str
    created_by: Optional[UUID] = None
    line_items: List[PurchaseOrderLineResponse] = []
    
    class Config:
        from_attributes = True


class PurchaseOrderListResponse(BaseModel):
    """Response schema for listing Purchase Orders"""
    items: List[PurchaseOrderResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

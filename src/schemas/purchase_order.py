// src/schemas/purchase_order.py
"""Purchase Order schemas."""
from typing import Optional, List
from datetime import date
from decimal import Decimal
from uuid import UUID
from pydantic import Field, ConfigDict

from src.schemas.base import BaseSchema, TimestampUUIDSchema
from src.models.enums import DocumentStatus


class PurchaseOrderLineBase(BaseSchema):
    """Base PO line schema."""
    
    line_number: int = Field(..., ge=1)
    product_code: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., min_length=1, max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=0)
    line_amount: Decimal = Field(..., ge=0)


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Schema for creating a PO line."""
    pass


class PurchaseOrderLineResponse(TimestampUUIDSchema):
    """Schema for PO line response."""
    
    purchase_order_id: UUID
    line_number: int
    product_code: str
    description: str
    quantity: Decimal
    unit_of_measure: str
    unit_price: Decimal
    line_amount: Decimal


class PurchaseOrderBase(BaseSchema):
    """Base PO schema."""
    
    po_number: str = Field(..., min_length=1, max_length=50)
    supplier_id: UUID
    order_date: date
    expected_delivery_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = Field(None, max_length=1000)


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a PO."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    lines: List[PurchaseOrderLineCreate] = Field(..., min_length=1)
    subtotal: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None


class PurchaseOrderUpdate(BaseSchema):
    """Schema for updating a PO."""
    
    po_number: Optional[str] = Field(None, min_length=1, max_length=50)
    supplier_id: Optional[UUID] = None
    order_date: Optional[date] = None
    expected_delivery_date: Optional[date] = None
    status: Optional[DocumentStatus] = None
    currency: Optional[str] = Field(None, max_length=3)
    notes: Optional[str] = Field(None, max_length=1000)


class PurchaseOrderResponse(TimestampUUIDSchema):
    """Schema for PO response."""
    
    po_number: str
    supplier_id: UUID
    order_date: date
    expected_delivery_date: Optional[date] = None
    status: DocumentStatus
    currency: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    notes: Optional[str] = None
    lines: List[PurchaseOrderLineResponse] = []


class PurchaseOrderListResponse(BaseSchema):
    """Schema for PO list response without lines."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    po_number: str
    supplier_id: UUID
    order_date: date
    expected_delivery_date: Optional[date] = None
    status: DocumentStatus
    currency: str
    total_amount: Decimal
    created_at: date
    updated_at: date

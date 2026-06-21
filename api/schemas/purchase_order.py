// api/schemas/purchase_order.py
"""Purchase Order Pydantic schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# Line schemas
class PurchaseOrderLineBase(BaseModel):
    """Base schema for PO line items."""
    
    line_number: int = Field(ge=1)
    item_code: Optional[str] = Field(None, max_length=50)
    item_description: str = Field(max_length=500)
    quantity_ordered: Decimal = Field(ge=0)
    unit_price: Decimal = Field(ge=0)
    tax_rate: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    expected_delivery_date: Optional[date] = None
    notes: Optional[str] = None


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Schema for creating a PO line item."""
    pass


class PurchaseOrderLineUpdate(BaseModel):
    """Schema for updating a PO line item."""
    
    item_code: Optional[str] = Field(None, max_length=50)
    item_description: Optional[str] = Field(None, max_length=500)
    quantity_ordered: Optional[Decimal] = Field(None, ge=0)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    quantity_delivered: Optional[Decimal] = Field(None, ge=0)
    quantity_invoiced: Optional[Decimal] = Field(None, ge=0)
    expected_delivery_date: Optional[date] = None
    notes: Optional[str] = None


class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    """Schema for PO line item response."""
    
    id: UUID
    purchase_order_id: UUID
    quantity_delivered: Decimal
    quantity_invoiced: Decimal
    line_total: Decimal
    tax_amount: Decimal
    remaining_quantity: Decimal
    remaining_to_invoice: Decimal
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


# PO schemas
class PurchaseOrderBase(BaseModel):
    """Base schema for Purchase Orders."""
    
    po_number: str = Field(max_length=50)
    supplier_id: UUID
    supplier_name: str = Field(max_length=255)
    supplier_code: Optional[str] = Field(None, max_length=50)
    order_date: date
    expected_delivery_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None
    metadata: Optional[dict] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a Purchase Order."""
    
    lines: List[PurchaseOrderLineCreate] = Field(default_factory=list)
    
    @field_validator("po_number")
    @classmethod
    def validate_po_number(cls, v: str) -> str:
        return v.strip().upper()


class PurchaseOrderUpdate(BaseModel):
    """Schema for updating a Purchase Order."""
    
    supplier_name: Optional[str] = Field(None, max_length=255)
    supplier_code: Optional[str] = Field(None, max_length=50)
    expected_delivery_date: Optional[date] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    metadata: Optional[dict] = None
    is_anchored: Optional[bool] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    """Schema for Purchase Order response."""
    
    id: UUID
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    status: str
    is_anchored: bool
    line_count: int
    remaining_amount: Decimal
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class PurchaseOrderDetailResponse(PurchaseOrderResponse):
    """Schema for detailed Purchase Order response with lines."""
    
    lines: List[PurchaseOrderLineResponse] = []
    
    model_config = {"from_attributes": True}


class PurchaseOrderListResponse(BaseModel):
    """Schema for paginated list of Purchase Orders."""
    
    items: List[PurchaseOrderResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

// api/schemas/purchase_order.py
"""Purchase Order schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


class PurchaseOrderLineBase(BaseModel):
    """Base PO line schema."""
    
    line_number: int = Field(..., ge=1)
    item_code: Optional[str] = Field(None, max_length=100)
    description: str = Field(..., min_length=1)
    quantity: Decimal = Field(..., gt=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=0)
    tax_rate: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    expected_delivery_date: Optional[date] = None


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Schema for creating a PO line."""
    pass


class PurchaseOrderLineUpdate(BaseModel):
    """Schema for updating a PO line."""
    
    item_code: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    expected_delivery_date: Optional[date] = None


class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    """Schema for PO line response."""
    
    id: UUID
    purchase_order_id: UUID
    line_total: Decimal
    tax_amount: Decimal
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class PurchaseOrderBase(BaseModel):
    """Base PO schema."""
    
    po_number: str = Field(..., min_length=1, max_length=100)
    supplier_id: UUID
    order_date: date
    expected_delivery_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a PO."""
    
    lines: List[PurchaseOrderLineCreate] = Field(default_factory=list)


class PurchaseOrderUpdate(BaseModel):
    """Schema for updating a PO."""
    
    supplier_id: Optional[UUID] = None
    order_date: Optional[date] = None
    expected_delivery_date: Optional[date] = None
    status: Optional[str] = None
    currency: Optional[str] = Field(None, max_length=3)
    notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    """Schema for PO response."""
    
    id: UUID
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class PurchaseOrderDetailResponse(PurchaseOrderResponse):
    """Schema for detailed PO response with lines."""
    
    lines: List[PurchaseOrderLineResponse] = []
    
    model_config = {"from_attributes": True}

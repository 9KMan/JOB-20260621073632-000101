// src/schemas/purchase_order.py
"""Purchase Order schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PurchaseOrderLineBase(BaseModel):
    """Base schema for PO line."""
    line_number: int
    sku: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    quantity_ordered: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    line_total: Decimal = Field(..., ge=0)


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Schema for creating a PO line."""
    pass


class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    """Schema for PO line response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    quantity_received: Decimal = Decimal("0")
    created_at: datetime
    updated_at: datetime
    
    @property
    def quantity_pending(self) -> Decimal:
        return self.quantity_ordered - self.quantity_received


class PurchaseOrderLineUpdate(BaseModel):
    """Schema for updating a PO line."""
    sku: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    quantity_ordered: Optional[Decimal] = Field(None, gt=0)
    quantity_received: Optional[Decimal] = Field(None, ge=0)
    unit_price: Optional[Decimal] = Field(None, ge=0)


class PurchaseOrderBase(BaseModel):
    """Base schema for Purchase Order."""
    po_number: str = Field(..., max_length=100)
    supplier_id: str = Field(..., max_length=100)
    supplier_name: str = Field(..., max_length=255)
    currency: str = Field(default="USD", max_length=3)
    total_amount: Decimal = Field(..., ge=0)
    order_date: date
    expected_date: Optional[date] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a Purchase Order."""
    lines: list[PurchaseOrderLineCreate] = Field(default_factory=list)


class PurchaseOrderUpdate(BaseModel):
    """Schema for updating a Purchase Order."""
    supplier_id: Optional[str] = Field(None, max_length=100)
    supplier_name: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(None, max_length=50)
    currency: Optional[str] = Field(None, max_length=3)
    total_amount: Optional[Decimal] = Field(None, ge=0)
    expected_date: Optional[date] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    """Schema for Purchase Order response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    lines: list[PurchaseOrderLineResponse] = Field(default_factory=list)


class PurchaseOrderListResponse(BaseModel):
    """Schema for paginated PO list."""
    items: list[PurchaseOrderResponse]
    total: int
    page: int
    page_size: int
    pages: int

# src/schemas/purchase_order.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


class PurchaseOrderLineBase(BaseModel):
    """Base schema for PO line."""
    line_number: int = Field(..., ge=1)
    product_code: str = Field(..., max_length=50)
    product_name: str = Field(..., max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=0)
    tax_rate: Decimal = Field(default=Decimal("0"))
    expected_delivery_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=500)


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Schema for creating PO line."""
    tax_amount: Optional[Decimal] = None


class PurchaseOrderLineUpdate(BaseModel):
    """Schema for updating PO line."""
    line_number: Optional[int] = Field(None, ge=1)
    product_code: Optional[str] = Field(None, max_length=50)
    product_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    tax_rate: Optional[Decimal] = None
    expected_delivery_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=500)


class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    """Schema for PO line response."""
    id: str
    purchase_order_id: str
    line_amount: Decimal
    tax_amount: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PurchaseOrderBase(BaseModel):
    """Base schema for Purchase Order."""
    po_number: str = Field(..., max_length=50)
    supplier_id: str = Field(..., max_length=36)
    supplier_name: str = Field(..., max_length=255)
    supplier_code: Optional[str] = Field(None, max_length=50)
    order_date: date
    expected_delivery_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = Field(None, max_length=1000)
    metadata: Optional[str] = Field(None, max_length=5000)


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating Purchase Order."""
    lines: List[PurchaseOrderLineCreate] = Field(default_factory=list)


class PurchaseOrderUpdate(BaseModel):
    """Schema for updating Purchase Order."""
    supplier_name: Optional[str] = Field(None, max_length=255)
    supplier_code: Optional[str] = Field(None, max_length=50)
    expected_delivery_date: Optional[date] = None
    status: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=1000)
    metadata: Optional[str] = Field(None, max_length=5000)


class PurchaseOrderResponse(PurchaseOrderBase):
    """Schema for Purchase Order response."""
    id: str
    status: str
    total_amount: Decimal
    tax_amount: Decimal
    created_at: datetime
    updated_at: datetime
    lines: List[PurchaseOrderLineResponse] = []

    class Config:
        from_attributes = True

// src/app/schemas/purchase_order.py
"""Purchase Order schemas."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict


class PurchaseOrderLineBase(BaseModel):
    """Base schema for PO line."""

    line_number: int
    product_code: str
    product_description: str
    quantity: Decimal
    unit_of_measure: str = "EA"
    unit_price: Decimal
    expected_delivery_date: Optional[date] = None
    metadata: Optional[dict] = None


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Schema for creating a PO line."""

    pass


class PurchaseOrderLineUpdate(BaseModel):
    """Schema for updating a PO line."""

    line_number: Optional[int] = None
    product_code: Optional[str] = None
    product_description: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit_of_measure: Optional[str] = None
    unit_price: Optional[Decimal] = None
    expected_delivery_date: Optional[date] = None
    metadata: Optional[dict] = None


class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    """Schema for PO line response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    purchase_order_id: uuid.UUID
    line_total: Decimal
    created_at: datetime
    updated_at: datetime


class PurchaseOrderBase(BaseModel):
    """Base schema for Purchase Order."""

    po_number: str
    supplier_id: str
    supplier_name: str
    supplier_address: Optional[str] = None
    order_date: date
    expected_delivery_date: Optional[date] = None
    currency: str = "USD"
    notes: Optional[str] = None
    metadata: Optional[dict] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a Purchase Order."""

    lines: List[PurchaseOrderLineCreate] = Field(default_factory=list)


class PurchaseOrderUpdate(BaseModel):
    """Schema for updating a Purchase Order."""

    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    supplier_address: Optional[str] = None
    status: Optional[str] = None
    expected_delivery_date: Optional[date] = None
    currency: Optional[str] = None
    notes: Optional[str] = None
    metadata: Optional[dict] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    """Schema for Purchase Order response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    lines: List[PurchaseOrderLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class PurchaseOrderListResponse(BaseModel):
    """Schema for paginated PO list."""

    items: List[PurchaseOrderResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

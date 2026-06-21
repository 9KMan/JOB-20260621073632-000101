// src/schemas/purchase_order.py
"""Purchase Order schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from src.schemas.common import BaseSchema, UUIDMixin


class PurchaseOrderLineBase(BaseModel):
    """Base schema for PO line items."""
    line_number: int
    sku: Optional[str] = None
    description: str
    quantity: Decimal
    unit_price: Decimal
    tax_amount: Decimal = Decimal("0")
    total_amount: Decimal
    uom: str = "EA"
    metadata: Optional[dict] = None


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Schema for creating PO line items."""
    pass


class PurchaseOrderLineUpdate(BaseModel):
    """Schema for updating PO line items."""
    sku: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit_price: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    uom: Optional[str] = None
    metadata: Optional[dict] = None


class PurchaseOrderLineResponse(UUIDMixin, BaseSchema):
    """Response schema for PO line items."""
    purchase_order_id: UUID
    line_number: int
    sku: Optional[str]
    description: str
    quantity: Decimal
    unit_price: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    uom: str
    metadata: Optional[dict]
    created_at: datetime
    updated_at: datetime


class PurchaseOrderBase(BaseModel):
    """Base schema for purchase orders."""
    po_number: str = Field(max_length=50)
    supplier_id: str = Field(max_length=100)
    supplier_name: str = Field(max_length=255)
    supplier_reference: Optional[str] = None
    order_date: date
    expected_delivery_date: Optional[date] = None
    subtotal: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    total_amount: Decimal = Decimal("0")
    currency: str = Field(default="USD", max_length=3)
    status: str = "OPEN"
    notes: Optional[str] = None
    metadata: Optional[dict] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a purchase order."""
    lines: list[PurchaseOrderLineCreate] = Field(default_factory=list)


class PurchaseOrderUpdate(BaseModel):
    """Schema for updating a purchase order."""
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    supplier_reference: Optional[str] = None
    expected_delivery_date: Optional[date] = None
    subtotal: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    currency: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    metadata: Optional[dict] = None


class PurchaseOrderResponse(UUIDMixin, BaseSchema):
    """Response schema for purchase orders."""
    po_number: str
    supplier_id: str
    supplier_name: str
    supplier_reference: Optional[str]
    order_date: date
    expected_delivery_date: Optional[date]
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    currency: str
    status: str
    notes: Optional[str]
    metadata: Optional[dict]
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    is_deleted: bool


class PurchaseOrderListResponse(BaseSchema):
    """Response schema for listing purchase orders."""
    id: UUID
    po_number: str
    supplier_id: str
    supplier_name: str
    order_date: date
    total_amount: Decimal
    currency: str
    status: str
    created_at: datetime

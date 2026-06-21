// src/app/schemas/purchase_order.py
"""
Purchase Order schemas for API request/response validation.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.base import BaseSchema, TimestampSchema, PaginationParams, PaginatedResponse
from app.schemas.supplier import SupplierBrief


# Line item schemas
class PurchaseOrderLineCreate(BaseSchema):
    """Schema for creating a PO line."""
    line_number: int = Field(..., ge=1)
    description: str = Field(..., min_length=1, max_length=500)
    sku: Optional[str] = Field(None, max_length=100)
    quantity: Decimal = Field(..., gt=0)
    unit_of_measure: str = Field(default="EA")
    unit_price: Decimal = Field(..., ge=0)
    tax_rate: Decimal = Field(default=Decimal("0.0000"), ge=0)


class PurchaseOrderLineUpdate(BaseSchema):
    """Schema for updating a PO line."""
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    sku: Optional[str] = Field(None, max_length=100)
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit_of_measure: Optional[str] = None
    unit_price: Optional[Decimal] = Field(None, ge=0)
    tax_rate: Optional[Decimal] = Field(None, ge=0)


class PurchaseOrderLineResponse(BaseSchema):
    """PO line response schema."""
    id: UUID
    line_number: int
    description: str
    sku: Optional[str]
    quantity: Decimal
    unit_of_measure: str
    unit_price: Decimal
    tax_rate: Decimal
    line_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    quantity_received: Decimal


# Header schemas
class PurchaseOrderCreate(BaseSchema):
    """Schema for creating a PO."""
    po_number: str = Field(..., min_length=1, max_length=50)
    supplier_id: UUID
    order_date: date
    expected_delivery_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None
    lines: List[PurchaseOrderLineCreate]


class PurchaseOrderUpdate(BaseSchema):
    """Schema for updating a PO."""
    supplier_id: Optional[UUID] = None
    order_date: Optional[date] = None
    expected_delivery_date: Optional[date] = None
    status: Optional[str] = None
    currency: Optional[str] = Field(None, max_length=3)
    notes: Optional[str] = None


class PurchaseOrderResponse(TimestampSchema):
    """PO response schema."""
    id: UUID
    po_number: str
    supplier_id: UUID
    order_date: date
    expected_delivery_date: Optional[date]
    status: str
    currency: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    notes: Optional[str]
    approved_by: Optional[UUID]
    approved_at: Optional[datetime]
    lines: List[PurchaseOrderLineResponse] = []
    supplier: Optional[SupplierBrief] = None


class PurchaseOrderBrief(BaseSchema):
    """Brief PO information."""
    id: UUID
    po_number: str
    total_amount: Decimal
    status: str


class PurchaseOrderListResponse(PaginatedResponse[PurchaseOrderResponse]):
    """Paginated PO list response."""
    pass


# Status update schema
class PurchaseOrderStatusUpdate(BaseSchema):
    """Schema for updating PO status."""
    status: str = Field(..., description="New status: draft, approved, closed, cancelled")

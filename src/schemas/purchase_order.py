// src/schemas/purchase_order.py
"""Purchase Order schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.base import BaseSchema, PaginatedResponse


class PurchaseOrderLineBase(BaseModel):
    """Base schema for PO line items."""

    line_number: int
    sku: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=0)
    line_amount: Decimal = Field(..., ge=0)
    tax_rate: Decimal = Field(default=Decimal("0.00"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    delivery_date: Optional[date] = None
    notes: Optional[str] = None


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Schema for creating PO line items."""

    pass


class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    """Schema for PO line item response."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    purchase_order_id: UUID
    created_at: datetime
    updated_at: datetime


class PurchaseOrderBase(BaseModel):
    """Base schema for Purchase Orders."""

    po_number: str = Field(..., max_length=50)
    supplier_id: UUID
    supplier_name: str = Field(..., max_length=255)
    supplier_reference: Optional[str] = Field(None, max_length=100)
    order_date: date
    expected_delivery_date: Optional[date] = None
    total_amount: Decimal = Field(..., ge=0)
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a Purchase Order."""

    lines: list[PurchaseOrderLineCreate] = Field(default_factory=list)


class PurchaseOrderUpdate(BaseModel):
    """Schema for updating a Purchase Order."""

    supplier_name: Optional[str] = Field(None, max_length=255)
    supplier_reference: Optional[str] = Field(None, max_length=100)
    expected_delivery_date: Optional[date] = None
    total_amount: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None
    status: Optional[str] = Field(None, max_length=20)
    lines: Optional[list[PurchaseOrderLineCreate]] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    """Schema for Purchase Order response."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    status: str
    open_amount: Decimal
    lines: list[PurchaseOrderLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class PurchaseOrderListResponse(PaginatedResponse[PurchaseOrderResponse]):
    """Paginated list of Purchase Orders."""

    pass

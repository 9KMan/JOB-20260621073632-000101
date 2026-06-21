// src/schemas/purchase_order.py
"""Purchase Order schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.common import BaseSchema, PaginatedResponse


class PurchaseOrderLineBase(BaseSchema):
    """Base schema for PO line items."""

    line_number: int = Field(..., ge=1)
    product_code: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    quantity: Decimal = Field(..., ge=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=0)
    line_total: Decimal = Field(..., ge=0)
    tax_rate: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    tax_amount: Decimal = Field(default=Decimal("0"), ge=0)
    expected_delivery_date: Optional[date] = None
    notes: Optional[str] = None


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Schema for creating PO line items."""

    pass


class PurchaseOrderLineUpdate(BaseSchema):
    """Schema for updating PO line items."""

    line_number: Optional[int] = Field(None, ge=1)
    product_code: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    quantity: Optional[Decimal] = Field(None, ge=0)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    line_total: Optional[Decimal] = Field(None, ge=0)
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    expected_delivery_date: Optional[date] = None
    notes: Optional[str] = None


class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    """Schema for PO line item responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    purchase_order_id: UUID
    created_at: datetime
    updated_at: datetime


class PurchaseOrderBase(BaseSchema):
    """Base schema for Purchase Orders."""

    po_number: str = Field(..., max_length=50)
    supplier_id: UUID
    supplier_name: str = Field(..., max_length=255)
    supplier_code: Optional[str] = Field(None, max_length=50)
    order_date: date
    expected_delivery_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    subtotal: Decimal = Field(default=Decimal("0"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0"), ge=0)
    total_amount: Decimal = Field(default=Decimal("0"), ge=0)
    status: str = Field(default="draft", max_length=20)
    notes: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating Purchase Orders."""

    lines: List[PurchaseOrderLineCreate] = Field(default_factory=list)


class PurchaseOrderUpdate(BaseSchema):
    """Schema for updating Purchase Orders."""

    supplier_id: Optional[UUID] = None
    supplier_name: Optional[str] = Field(None, max_length=255)
    supplier_code: Optional[str] = Field(None, max_length=50)
    order_date: Optional[date] = None
    expected_delivery_date: Optional[date] = None
    currency: Optional[str] = Field(None, max_length=3)
    subtotal: Optional[Decimal] = Field(None, ge=0)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    total_amount: Optional[Decimal] = Field(None, ge=0)
    status: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    """Schema for Purchase Order responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    deleted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    lines: List[PurchaseOrderLineResponse] = Field(default_factory=list)


class PurchaseOrderListResponse(PaginatedResponse[PurchaseOrderResponse]):
    """Schema for paginated PO list response."""

    pass


class PurchaseOrderSummary(BaseSchema):
    """Schema for PO summary (minimal data)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    po_number: str
    supplier_name: str
    total_amount: Decimal
    status: str
    order_date: date

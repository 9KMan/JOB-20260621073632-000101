// src/app/schemas/purchase_order.py
"""Purchase Order schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PurchaseOrderLineBase(BaseModel):
    """Base PO line schema."""

    line_number: int = Field(..., ge=1)
    description: str = Field(..., min_length=1, max_length=500)
    sku: Optional[str] = Field(None, max_length=100)
    quantity: Decimal = Field(..., ge=0)
    unit_price: Decimal = Field(..., ge=0)
    line_total: Decimal = Field(..., ge=0)
    uom: str = Field(default="EA", max_length=20)
    tax_rate: Decimal = Field(default=Decimal("0"), ge=0)


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Schema for creating a PO line."""

    pass


class PurchaseOrderLineUpdate(BaseModel):
    """Schema for updating a PO line."""

    line_number: Optional[int] = Field(None, ge=1)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    sku: Optional[str] = Field(None, max_length=100)
    quantity: Optional[Decimal] = Field(None, ge=0)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    line_total: Optional[Decimal] = Field(None, ge=0)
    uom: Optional[str] = Field(None, max_length=20)
    tax_rate: Optional[Decimal] = Field(None, ge=0)


class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    """PO line response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    purchase_order_id: UUID
    created_at: datetime
    updated_at: datetime


class PurchaseOrderBase(BaseModel):
    """Base purchase order schema."""

    po_number: str = Field(..., min_length=1, max_length=100)
    supplier_id: UUID
    order_date: date
    expected_delivery_date: Optional[date] = None
    status: str = Field(default="DRAFT", max_length=50)
    total_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None
    terms: Optional[str] = Field(None, max_length=255)


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a purchase order."""

    lines: list[PurchaseOrderLineCreate] = []


class PurchaseOrderUpdate(BaseModel):
    """Schema for updating a purchase order."""

    po_number: Optional[str] = Field(None, min_length=1, max_length=100)
    supplier_id: Optional[UUID] = None
    order_date: Optional[date] = None
    expected_delivery_date: Optional[date] = None
    status: Optional[str] = Field(None, max_length=50)
    total_amount: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    notes: Optional[str] = None
    terms: Optional[str] = Field(None, max_length=255)
    lines: Optional[list[PurchaseOrderLineCreate]] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    """Purchase order response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class PurchaseOrderDetailResponse(PurchaseOrderResponse):
    """Purchase order detail response with lines."""

    lines: list[PurchaseOrderLineResponse] = []
    supplier_name: Optional[str] = None
    supplier_code: Optional[str] = None


class PurchaseOrderListResponse(BaseModel):
    """Schema for PO list response."""

    items: list[PurchaseOrderDetailResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

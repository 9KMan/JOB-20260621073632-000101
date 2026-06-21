// src/schemas/purchase_order.py
"""
FinaRo AP Automation Core Engine
Purchase Order Pydantic Schemas
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.base import BaseSchema


class PurchaseOrderLineBase(BaseSchema):
    """Base schema for Purchase Order Line."""
    line_number: int = Field(..., ge=1)
    internal_reference: Optional[str] = None
    product_id: Optional[UUID] = None
    product_code: Optional[str] = None
    product_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    quantity_ordered: Decimal = Field(..., ge=Decimal('0'))
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=Decimal('0'))
    tax_rate: Decimal = Field(default=Decimal('0'), ge=Decimal('0'))
    expected_delivery_date: Optional[date] = None


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Schema for creating a Purchase Order Line."""
    pass


class PurchaseOrderLineUpdate(BaseSchema):
    """Schema for updating a Purchase Order Line."""
    line_number: Optional[int] = Field(None, ge=1)
    internal_reference: Optional[str] = None
    product_id: Optional[UUID] = None
    product_code: Optional[str] = None
    product_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    quantity_ordered: Optional[Decimal] = Field(None, ge=Decimal('0'))
    quantity_received: Optional[Decimal] = Field(None, ge=Decimal('0'))
    quantity_invoiced: Optional[Decimal] = Field(None, ge=Decimal('0'))
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    unit_price: Optional[Decimal] = Field(None, ge=Decimal('0'))
    tax_rate: Optional[Decimal] = Field(None, ge=Decimal('0'))
    expected_delivery_date: Optional[date] = None
    status: Optional[str] = None


class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    """Schema for Purchase Order Line response."""
    id: UUID
    po_id: UUID
    quantity_received: Decimal
    quantity_invoiced: Decimal
    line_total: Decimal
    tax_amount: Decimal
    status: str
    quantity_remaining: Decimal
    created_at: datetime
    updated_at: datetime


class PurchaseOrderBase(BaseSchema):
    """Base schema for Purchase Order."""
    po_number: str = Field(..., min_length=1, max_length=50)
    supplier_id: UUID
    supplier_name: str = Field(..., min_length=1, max_length=255)
    supplier_code: Optional[str] = None
    company_id: UUID
    company_name: str = Field(..., min_length=1, max_length=255)
    po_date: date
    expected_delivery_date: Optional[date] = None
    latest_delivery_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    payment_terms: Optional[str] = None
    delivery_terms: Optional[str] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    department: Optional[str] = None
    cost_center: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a Purchase Order."""
    lines: List[PurchaseOrderLineCreate] = Field(default_factory=list)


class PurchaseOrderUpdate(BaseSchema):
    """Schema for updating a Purchase Order."""
    po_number: Optional[str] = Field(None, min_length=1, max_length=50)
    supplier_id: Optional[UUID] = None
    supplier_name: Optional[str] = Field(None, min_length=1, max_length=255)
    supplier_code: Optional[str] = None
    po_date: Optional[date] = None
    expected_delivery_date: Optional[date] = None
    latest_delivery_date: Optional[date] = None
    status: Optional[str] = None
    currency: Optional[str] = Field(None, max_length=3)
    payment_terms: Optional[str] = None
    delivery_terms: Optional[str] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    department: Optional[str] = None
    cost_center: Optional[str] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    """Schema for Purchase Order response."""
    id: UUID
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    open_amount: Decimal
    is_open: bool
    lines: List[PurchaseOrderLineResponse]
    created_at: datetime
    updated_at: datetime
    
    @field_validator('lines', mode='before')
    @classmethod
    def validate_lines(cls, v):
        if v is None:
            return []
        return v


class PurchaseOrderListResponse(BaseSchema):
    """Schema for Purchase Order list item response."""
    id: UUID
    po_number: str
    supplier_id: UUID
    supplier_name: str
    po_date: date
    status: str
    total_amount: Decimal
    currency: str
    department: Optional[str]
    created_at: datetime

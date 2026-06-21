// src/schemas/purchase_order.py
"""Purchase Order schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import Field, ConfigDict

from src.schemas.common import BaseSchema
from src.schemas.supplier import SupplierResponse
from src.models.enums import DocumentStatus


class PurchaseOrderLineBase(BaseSchema):
    """Base PO line schema."""
    line_number: int = Field(..., ge=1)
    product_code: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=0)
    tax_rate: Decimal = Field(default=Decimal("0.0000"), ge=0)
    expected_delivery_date: Optional[date] = None


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """PO line creation schema."""
    pass


class PurchaseOrderLineUpdate(BaseSchema):
    """PO line update schema."""
    line_number: Optional[int] = Field(None, ge=1)
    product_code: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    tax_rate: Optional[Decimal] = Field(None, ge=0)
    expected_delivery_date: Optional[date] = None


class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    """PO line response schema."""
    id: UUID
    purchase_order_id: UUID
    line_total: Decimal
    tax_amount: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderBase(BaseSchema):
    """Base PO schema."""
    po_number: str = Field(..., min_length=1, max_length=50)
    supplier_id: UUID
    order_date: date
    expected_delivery_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """PO creation schema."""
    lines: list[PurchaseOrderLineCreate] = Field(default_factory=list)


class PurchaseOrderUpdate(BaseSchema):
    """PO update schema."""
    po_number: Optional[str] = Field(None, min_length=1, max_length=50)
    supplier_id: Optional[UUID] = None
    order_date: Optional[date] = None
    expected_delivery_date: Optional[date] = None
    status: Optional[DocumentStatus] = None
    currency: Optional[str] = Field(None, max_length=3)
    notes: Optional[str] = None


class PurchaseOrderLineWithRelations(PurchaseOrderLineResponse):
    """PO line with relationships."""
    pass


class PurchaseOrderResponse(PurchaseOrderBase):
    """PO response schema."""
    id: UUID
    status: DocumentStatus
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    approved_at: Optional[datetime] = None
    approved_by_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    lines: list[PurchaseOrderLineResponse] = Field(default_factory=list)
    supplier: Optional[SupplierResponse] = None

    model_config = ConfigDict(from_attributes=True)

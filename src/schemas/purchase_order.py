// src/schemas/purchase_order.py
"""Purchase Order schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from src.schemas.common import BaseSchema, TimestampMixin


class PurchaseOrderLineBase(BaseSchema):
    """Base PO line schema."""
    line_number: int
    item_code: str
    item_description: str
    quantity: Decimal
    unit_of_measure: str = "EA"
    unit_price: Decimal
    tax_code: Optional[str] = None
    tax_rate: Decimal = Decimal("0.00")


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Schema for creating a PO line."""
    po_line_id: Optional[UUID] = None


class PurchaseOrderLineUpdate(BaseSchema):
    """Schema for updating a PO line."""
    item_code: Optional[str] = None
    item_description: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit_of_measure: Optional[str] = None
    unit_price: Optional[Decimal] = None
    tax_code: Optional[str] = None
    tax_rate: Optional[Decimal] = None
    delivered_quantity: Optional[Decimal] = None
    invoiced_quantity: Optional[Decimal] = None


class PurchaseOrderLineResponse(PurchaseOrderLineBase, TimestampMixin):
    """Schema for PO line response."""
    id: UUID
    purchase_order_id: UUID
    line_amount: Decimal
    tax_amount: Decimal
    delivered_quantity: Decimal
    invoiced_quantity: Decimal
    status: str

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderBase(BaseSchema):
    """Base PO schema."""
    po_number: str
    supplier_id: str
    supplier_name: str
    supplier_code: Optional[str] = None
    order_date: date
    expected_delivery_date: Optional[date] = None
    currency: str = "USD"
    notes: Optional[str] = None
    internal_reference: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a PO."""
    lines: list[PurchaseOrderLineCreate]
    created_by_id: Optional[UUID] = None


class PurchaseOrderUpdate(BaseSchema):
    """Schema for updating a PO."""
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    supplier_code: Optional[str] = None
    expected_delivery_date: Optional[date] = None
    actual_delivery_date: Optional[date] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    internal_reference: Optional[str] = None


class PurchaseOrderResponse(PurchaseOrderBase, TimestampMixin):
    """Schema for PO response."""
    id: UUID
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    remaining_amount: Decimal
    created_by_id: Optional[UUID] = None
    approved_by_id: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    lines: list[PurchaseOrderLineResponse] = []

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderSummary(BaseSchema):
    """Summary of PO for lists."""
    id: UUID
    po_number: str
    supplier_name: str
    order_date: date
    status: str
    total_amount: Decimal
    remaining_amount: Decimal
    matched_amount: Decimal = Decimal("0.00")
    match_percentage: float = 0.0

    model_config = ConfigDict(from_attributes=True)

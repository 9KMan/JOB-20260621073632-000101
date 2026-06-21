// src/app/schemas/purchase_order.py
"""
Purchase Order schemas.
"""
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field

from app.schemas.common import BaseSchema, TimestampMixin
from app.schemas.supplier import SupplierResponse


class PurchaseOrderLineBase(BaseModel):
    """Base PO line schema."""
    line_number: int = Field(..., ge=1)
    product_code: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., gt=0)
    expected_delivery_date: Optional[date] = None


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """PO line creation schema."""
    pass


class PurchaseOrderLineResponse(PurchaseOrderLineBase, TimestampMixin):
    """PO line response schema."""
    id: str
    purchase_order_id: str
    line_total: Decimal


class PurchaseOrderBase(BaseModel):
    """Base PO schema."""
    po_number: str = Field(..., min_length=1, max_length=50)
    supplier_id: str
    order_date: date
    expected_delivery_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None
    erp_reference: Optional[str] = Field(default=None, max_length=100)


class PurchaseOrderCreate(PurchaseOrderBase):
    """PO creation schema."""
    lines: List[PurchaseOrderLineCreate]


class PurchaseOrderUpdate(BaseModel):
    """PO update schema."""
    po_number: Optional[str] = Field(default=None, min_length=1, max_length=50)
    supplier_id: Optional[str] = None
    order_date: Optional[date] = None
    expected_delivery_date: Optional[date] = None
    status: Optional[str] = None
    currency: Optional[str] = Field(default=None, max_length=3)
    notes: Optional[str] = None
    erp_reference: Optional[str] = Field(default=None, max_length=100)


class PurchaseOrderResponse(PurchaseOrderBase, TimestampMixin):
    """PO response schema."""
    id: str
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    supplier: Optional[SupplierResponse] = None
    lines: List[PurchaseOrderLineResponse] = []
    matched_invoices_count: Optional[int] = 0
    is_open: bool = True

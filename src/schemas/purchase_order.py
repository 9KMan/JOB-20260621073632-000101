// src/schemas/purchase_order.py
// src/schemas/purchase_order.py
"""Purchase Order schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.base import BaseSchema


class PurchaseOrderLineBase(BaseSchema):
    """Base purchase order line schema."""
    line_number: int
    item_code: Optional[str] = None
    item_description: str
    quantity: Decimal
    unit_of_measure: str = "EA"
    unit_price: Decimal
    tax_rate: Decimal = Decimal("0.00")
    tax_amount: Decimal = Decimal("0.00")
    line_total: Decimal
    quantity_received: Decimal = Decimal("0")
    quantity_invoiced: Decimal = Decimal("0")
    status: str = "open"


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Purchase order line creation schema."""
    pass


class PurchaseOrderLineUpdate(BaseSchema):
    """Purchase order line update schema."""
    item_code: Optional[str] = None
    item_description: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit_of_measure: Optional[str] = None
    unit_price: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    quantity_received: Optional[Decimal] = None
    quantity_invoiced: Optional[Decimal] = None
    status: Optional[str] = None


class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    """Purchase order line response schema."""
    id: str
    purchase_order_id: str
    created_at: datetime
    updated_at: datetime


class PurchaseOrderBase(BaseSchema):
    """Base purchase order schema."""
    po_number: str
    supplier_id: str
    supplier_name: str
    supplier_code: Optional[str] = None
    po_date: date
    expected_delivery_date: Optional[date] = None
    status: str = "open"
    currency: str = "USD"
    notes: Optional[str] = None
    delivery_address: Optional[str] = None
    terms: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Purchase order creation schema."""
    subtotal: Decimal = Decimal("0.00")
    tax_amount: Decimal = Decimal("0.00")
    total_amount: Decimal
    lines: List[PurchaseOrderLineCreate] = Field(default_factory=list)


class PurchaseOrderUpdate(BaseSchema):
    """Purchase order update schema."""
    supplier_name: Optional[str] = None
    supplier_code: Optional[str] = None
    expected_delivery_date: Optional[date] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    delivery_address: Optional[str] = None
    terms: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    """Purchase order response schema."""
    id: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    total_received: Decimal
    total_invoiced: Decimal
    created_by: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    lines: List[PurchaseOrderLineResponse] = Field(default_factory=list)
    is_open: bool = Field(default=True, exclude=True)
    remaining_balance: Decimal = Field(default=Decimal("0.00"), exclude=True)

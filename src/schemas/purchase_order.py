// src/schemas/purchase_order.py
"""Purchase Order schemas."""
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from src.schemas.common import BaseSchema, PaginatedResponse, TimestampMixin, SoftDeleteMixin
from src.schemas.supplier import SupplierSummary


class PurchaseOrderLineBase(BaseSchema):
    """Base PO line schema."""
    line_number: int = Field(..., ge=1)
    item_code: Optional[str] = Field(None, max_length=100)
    description: str = Field(..., min_length=1)
    quantity: Decimal = Field(..., ge=Decimal("0"))
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=Decimal("0"))
    line_total: Decimal = Field(..., ge=Decimal("0"))
    tax_rate: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    tax_amount: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    expected_quantity: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    received_quantity: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Schema for creating PO line."""
    pass


class PurchaseOrderLineResponse(PurchaseOrderLineBase, TimestampMixin):
    """Schema for PO line response."""
    id: UUID
    po_id: UUID


class PurchaseOrderBase(BaseSchema):
    """Base PO schema."""
    po_number: str = Field(..., min_length=1, max_length=50)
    supplier_id: UUID
    order_date: str  # ISO date string
    expected_delivery_date: Optional[str] = None
    currency: str = Field(default="USD", max_length=3)
    subtotal: Decimal = Field(default=Decimal("0"))
    tax_amount: Decimal = Field(default=Decimal("0"))
    total_amount: Decimal = Field(default=Decimal("0"))
    notes: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a PO."""
    lines: List[PurchaseOrderLineCreate] = Field(default_factory=list)


class PurchaseOrderUpdate(BaseSchema):
    """Schema for updating a PO."""
    supplier_id: Optional[UUID] = None
    order_date: Optional[str] = None
    expected_delivery_date: Optional[str] = None
    currency: Optional[str] = Field(None, max_length=3)
    subtotal: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    notes: Optional[str] = None


class PurchaseOrderLineSummary(BaseSchema):
    """Lightweight PO line summary."""
    id: UUID
    line_number: int
    description: str
    quantity: Decimal
    received_quantity: Decimal
    unit_price: Decimal


class PurchaseOrderResponse(PurchaseOrderBase, TimestampMixin, SoftDeleteMixin):
    """Schema for PO response."""
    id: UUID
    status: str
    supplier: Optional[SupplierSummary] = None
    lines: List[PurchaseOrderLineResponse] = Field(default_factory=list)
    matched_invoices_count: Optional[int] = 0
    total_matched_amount: Optional[Decimal] = Decimal("0")


class PurchaseOrderListResponse(PaginatedResponse[PurchaseOrderResponse]):
    """Schema for paginated PO list."""
    pass


class PurchaseOrderSummary(BaseSchema):
    """Lightweight PO summary."""
    id: UUID
    po_number: str
    status: str
    total_amount: Decimal
    supplier_name: Optional[str] = None

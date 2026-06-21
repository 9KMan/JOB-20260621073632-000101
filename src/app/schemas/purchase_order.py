# src/app/schemas/purchase_order.py
"""Purchase Order schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.app.schemas.common import BaseSchema, TimestampMixin, UUIDMixin
from src.app.models.enums import DocumentStatus, LineStatus


class PurchaseOrderLineBase(BaseSchema):
    """Base PO line schema."""
    line_number: int = Field(..., ge=1)
    description: str = Field(..., min_length=1, max_length=500)
    sku: Optional[str] = Field(None, max_length=100)
    quantity_ordered: Decimal = Field(..., ge=0)
    quantity_delivered: Decimal = Field(default=Decimal("0.000"), ge=0)
    quantity_invoiced: Decimal = Field(default=Decimal("0.000"), ge=0)
    unit_price: Decimal = Field(..., ge=0)
    line_amount: Decimal = Field(..., ge=0)
    status: LineStatus = Field(default=LineStatus.PENDING)


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Schema for creating a PO line."""
    pass


class PurchaseOrderLineUpdate(BaseSchema):
    """Schema for updating a PO line."""
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    sku: Optional[str] = Field(None, max_length=100)
    quantity_ordered: Optional[Decimal] = Field(None, ge=0)
    quantity_delivered: Optional[Decimal] = Field(None, ge=0)
    quantity_invoiced: Optional[Decimal] = Field(None, ge=0)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    line_amount: Optional[Decimal] = Field(None, ge=0)
    status: Optional[LineStatus] = None


class PurchaseOrderLineRead(UUIDMixin, TimestampMixin, PurchaseOrderLineBase):
    """Schema for reading a PO line."""
    po_id: UUID
    deleted_at: Optional[datetime] = None
    is_deleted: bool = False


class PurchaseOrderBase(BaseSchema):
    """Base PO schema."""
    supplier_id: str = Field(..., min_length=1, max_length=100)
    supplier_name: str = Field(..., min_length=1, max_length=255)
    po_number: str = Field(..., min_length=1, max_length=100)
    po_date: date
    currency: str = Field(default="USD", min_length=3, max_length=3)
    total_amount: Decimal = Field(..., ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    status: DocumentStatus = Field(default=DocumentStatus.OPEN)
    notes: Optional[str] = None
    metadata: Optional[dict] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a PO."""
    lines: list[PurchaseOrderLineCreate] = Field(default_factory=list)


class PurchaseOrderUpdate(BaseSchema):
    """Schema for updating a PO."""
    supplier_id: Optional[str] = Field(None, min_length=1, max_length=100)
    supplier_name: Optional[str] = Field(None, min_length=1, max_length=255)
    po_number: Optional[str] = Field(None, min_length=1, max_length=100)
    po_date: Optional[date] = None
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    total_amount: Optional[Decimal] = Field(None, ge=0)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    status: Optional[DocumentStatus] = None
    notes: Optional[str] = None
    metadata: Optional[dict] = None


class PurchaseOrderRead(UUIDMixin, TimestampMixin, PurchaseOrderBase):
    """Schema for reading a PO."""
    deleted_at: Optional[datetime] = None
    is_deleted: bool = False
    lines: list[PurchaseOrderLineRead] = Field(default_factory=list)

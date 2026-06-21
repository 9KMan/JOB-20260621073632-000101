// src/schemas/purchase_order.py
"""Purchase Order schemas."""
import uuid
import decimal
from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict, field_validator

from src.models.enums import DocumentStatus


class PurchaseOrderLineBase(BaseModel):
    """Base schema for PO line."""
    line_number: int = Field(..., ge=1)
    product_code: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    quantity: decimal.Decimal = Field(..., gt=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: decimal.Decimal = Field(..., ge=0)
    line_amount: decimal.Decimal = Field(..., ge=0)
    tax_rate: decimal.Decimal = Field(default=decimal.Decimal("0.0000"), ge=0)
    tax_amount: decimal.Decimal = Field(default=decimal.Decimal("0.00"), ge=0)
    expected_delivery_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=500)


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Schema for creating a PO line."""
    pass


class PurchaseOrderLineUpdate(BaseModel):
    """Schema for updating a PO line."""
    product_code: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    quantity: Optional[decimal.Decimal] = Field(None, gt=0)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    unit_price: Optional[decimal.Decimal] = Field(None, ge=0)
    line_amount: Optional[decimal.Decimal] = Field(None, ge=0)
    tax_rate: Optional[decimal.Decimal] = Field(None, ge=0)
    tax_amount: Optional[decimal.Decimal] = Field(None, ge=0)
    expected_delivery_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=500)


class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    """Schema for PO line response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    purchase_order_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class PurchaseOrderBase(BaseModel):
    """Base schema for Purchase Order."""
    po_number: str = Field(..., min_length=1, max_length=50)
    supplier_id: str = Field(..., min_length=1, max_length=100)
    supplier_name: str = Field(..., min_length=1, max_length=255)
    supplier_reference: Optional[str] = Field(None, max_length=100)
    order_date: date
    expected_delivery_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = Field(None, max_length=1000)
    metadata: Optional[str] = Field(None, max_length=2000)


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a Purchase Order."""
    total_amount: decimal.Decimal = Field(default=decimal.Decimal("0.00"), ge=0)
    status: DocumentStatus = DocumentStatus.SUBMITTED
    lines: List[PurchaseOrderLineCreate] = Field(default_factory=list)


class PurchaseOrderUpdate(BaseModel):
    """Schema for updating a Purchase Order."""
    supplier_id: Optional[str] = Field(None, max_length=100)
    supplier_name: Optional[str] = Field(None, max_length=255)
    supplier_reference: Optional[str] = Field(None, max_length=100)
    order_date: Optional[date] = None
    expected_delivery_date: Optional[date] = None
    total_amount: Optional[decimal.Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    status: Optional[DocumentStatus] = None
    notes: Optional[str] = Field(None, max_length=1000)
    metadata: Optional[str] = Field(None, max_length=2000)


class PurchaseOrderResponse(PurchaseOrderBase):
    """Schema for Purchase Order response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    total_amount: decimal.Decimal
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    lines: List[PurchaseOrderLineResponse] = Field(default_factory=list)

    @field_validator("lines", mode="before")
    @classmethod
    def validate_lines(cls, v):
        return v if v else []

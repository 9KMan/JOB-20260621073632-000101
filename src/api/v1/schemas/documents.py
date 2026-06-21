# src/api/v1/schemas/documents.py
from datetime import date, datetime
from decimal import Decimal
from typing import Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


T = TypeVar("T")


# Base Line Schema
class BaseLineSchema(BaseModel):
    """Base schema for document lines."""
    line_number: int = Field(..., ge=1)
    item_code: str = Field(..., max_length=100)
    item_description: str = Field(..., max_length=500)
    quantity: Decimal = Field(..., ge=Decimal("0"))
    unit_price: Decimal = Field(..., ge=Decimal("0"))
    line_amount: Decimal = Field(..., ge=Decimal("0"))
    tax_code: Optional[str] = Field(None, max_length=50)
    tax_rate: Decimal = Field(default=Decimal("0.0000"), ge=Decimal("0"))
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"))


class PurchaseOrderLineCreate(BaseLineSchema):
    """Schema for creating PO line."""
    pass


class PurchaseOrderLineResponse(BaseLineSchema):
    """Schema for PO line response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    quantity_ordered: Decimal
    quantity_delivered: Decimal
    quantity_remaining: Decimal
    created_at: datetime
    updated_at: datetime


# Purchase Order Schemas
class PurchaseOrderBase(BaseModel):
    """Base schema for Purchase Order."""
    po_number: str = Field(..., max_length=50)
    supplier_id: str = Field(..., max_length=100)
    supplier_name: str = Field(..., max_length=255)
    supplier_address: Optional[str] = None
    supplier_tax_id: Optional[str] = Field(None, max_length=50)
    order_date: date
    expected_delivery_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a Purchase Order."""
    lines: List[PurchaseOrderLineCreate] = Field(..., min_length=1)

    @field_validator("lines")
    @classmethod
    def validate_lines(cls, v: List[PurchaseOrderLineCreate]) -> List[PurchaseOrderLineCreate]:
        for i, line in enumerate(v):
            expected_amount = line.quantity * line.unit_price
            if abs(line.line_amount - expected_amount) > Decimal("0.01"):
                raise ValueError(f"Line {i+1}: line_amount ({line.line_amount}) doesn't match quantity * unit_price ({expected_amount})")
        return v


class PurchaseOrderUpdate(BaseModel):
    """Schema for updating a Purchase Order."""
    supplier_name: Optional[str] = Field(None, max_length=255)
    supplier_address: Optional[str] = None
    supplier_tax_id: Optional[str] = Field(None, max_length=50)
    expected_delivery_date: Optional[date] = None
    currency: Optional[str] = Field(None, max_length=3)
    status: Optional[str] = None
    notes: Optional[str] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    """Schema for Purchase Order response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    status: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    lines: List[PurchaseOrderLineResponse] = []


class PurchaseOrderListResponse(PaginatedResponse[PurchaseOrderResponse]):
    """Paginated list of Purchase Orders."""
    pass


# Invoice Schemas
class InvoiceLineCreate(BaseLineSchema):
    """Schema for creating Invoice line."""
    pass


class InvoiceLineResponse(BaseLineSchema):
    """Schema for Invoice line response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class InvoiceBase(BaseModel):
    """Base schema for Invoice."""
    invoice_number: str = Field(..., max_length=50)
    supplier_id: str = Field(..., max_length=100)
    supplier_name: str = Field(..., max_length=255)
    supplier_address: Optional[str] = None
    supplier_tax_id: Optional[str] = Field(None, max_length=50)
    invoice_date: date
    due_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating an Invoice."""
    lines: List[InvoiceLineCreate] = Field(..., min_length=1)


class InvoiceUpdate(BaseModel):
    """Schema for updating an Invoice."""
    supplier_name: Optional[str] = Field(None, max_length=255)
    supplier_address: Optional[str] = None
    supplier_tax_id: Optional[str] = Field(None, max_length=50)
    due_date: Optional[date] = None
    currency: Optional[str] = Field(None, max_length=3)
    status: Optional[str] = None
    notes: Optional[str] = None


class InvoiceResponse(InvoiceBase):
    """Schema for Invoice response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    status: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    lines: List[InvoiceLineResponse] = []


class InvoiceListResponse(PaginatedResponse[InvoiceResponse]):
    """Paginated list of Invoices."""
    pass


# Delivery Note Schemas
class DeliveryNoteLineBase(BaseModel):
    """Base schema for Delivery Note line."""
    line_number: int = Field(..., ge=1)
    item_code: str = Field(..., max_length=100)
    item_description: str = Field(..., max_length=500)
    quantity_delivered: Decimal = Field(..., ge=Decimal("0"))
    quantity_accepted: Optional[Decimal] = None
    quantity_rejected: Decimal = Field(default=Decimal("0"))
    unit_of_measure: str = Field(default="EA", max_length=20)
    notes: Optional[str] = None


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating Delivery Note line."""
    pass


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """Schema for Delivery Note line response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class DeliveryNoteBase(BaseModel):
    """Base schema for Delivery Note."""
    dn_number: str = Field(..., max_length=50)
    supplier_id: str = Field(..., max_length=100)
    supplier_name: str = Field(..., max_length=255)
    supplier_address: Optional[str] = None
    delivery_date: date
    received_by: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating a Delivery Note."""
    lines: List[DeliveryNoteLineCreate] = Field(..., min_length=1)


class DeliveryNoteUpdate(BaseModel):
    """Schema for updating a Delivery Note."""
    supplier_name: Optional[str] = Field(None, max_length=255)
    supplier_address: Optional[str] = None
    delivery_date: Optional[date] = None
    received_by: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = None
    notes: Optional[str] = None


class DeliveryNoteResponse(DeliveryNoteBase):
    """Schema for Delivery Note response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    total_quantity: Decimal
    total_items: int
    status: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    lines: List[DeliveryNoteLineResponse] = []


class DeliveryNoteListResponse(PaginatedResponse[DeliveryNoteResponse]):
    """Paginated list of Delivery Notes."""
    pass


# Import for pagination
from src.api.v1.schemas.common import PaginatedResponse

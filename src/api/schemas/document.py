// src/api/schemas/document.py
"""Document API schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.api.schemas.common import BaseSchema
from app.models.document import DocumentStatus


class DocumentStatusEnum(str, Enum):
    """Document status enum for API."""

    DRAFT = "DRAFT"
    PENDING = "PENDING"
    MATCHED = "MATCHED"
    PARTIALLY_MATCHED = "PARTIALLY_MATCHED"
    CONFIRMED = "CONFIRMED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DISPUTED = "DISPUTED"
    CANCELLED = "CANCELLED"


# Base schemas
class POLineBase(BaseSchema):
    """PO Line base schema."""

    line_number: int = Field(..., ge=1)
    product_code: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    quantity: Decimal = Field(..., gt=0, decimal_places=3)
    unit_price: Decimal = Field(..., ge=0, decimal_places=2)
    uom: str = Field(default="EA", max_length=20)


class POLineCreate(POLineBase):
    """PO Line create schema."""

    pass


class POLineResponse(POLineBase):
    """PO Line response schema."""

    id: str
    po_id: str
    line_total: Decimal
    created_at: datetime
    updated_at: datetime


class PurchaseOrderBase(BaseSchema):
    """Purchase Order base schema."""

    po_number: str = Field(..., max_length=100)
    supplier_id: str = Field(..., max_length=36)
    supplier_name: str = Field(..., max_length=255)
    order_date: date
    expected_delivery_date: Optional[date] = None
    total_amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None
    metadata_: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Purchase Order create schema."""

    lines: list[POLineCreate]


class PurchaseOrderUpdate(BaseSchema):
    """Purchase Order update schema."""

    supplier_name: Optional[str] = Field(None, max_length=255)
    expected_delivery_date: Optional[date] = None
    total_amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    currency: Optional[str] = Field(None, max_length=3)
    status: Optional[DocumentStatusEnum] = None
    notes: Optional[str] = None
    metadata_: Optional[str] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    """Purchase Order response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    status: DocumentStatusEnum
    lines: list[POLineResponse] = []
    created_at: datetime
    updated_at: datetime


# Invoice schemas
class InvoiceLineBase(BaseSchema):
    """Invoice Line base schema."""

    line_number: int = Field(..., ge=1)
    product_code: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    quantity: Decimal = Field(..., gt=0, decimal_places=3)
    unit_price: Decimal = Field(..., ge=0, decimal_places=2)
    uom: str = Field(default="EA", max_length=20)


class InvoiceLineCreate(InvoiceLineBase):
    """Invoice Line create schema."""

    pass


class InvoiceLineResponse(InvoiceLineBase):
    """Invoice Line response schema."""

    id: str
    invoice_id: str
    line_total: Decimal
    created_at: datetime
    updated_at: datetime


class InvoiceBase(BaseSchema):
    """Invoice base schema."""

    invoice_number: str = Field(..., max_length=100)
    supplier_id: str = Field(..., max_length=36)
    supplier_name: str = Field(..., max_length=255)
    po_id: Optional[str] = None
    invoice_date: date
    due_date: Optional[date] = None
    total_amount: Decimal = Field(..., gt=0, decimal_places=2)
    tax_amount: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None
    metadata_: Optional[str] = None

    @field_validator("po_id")
    @classmethod
    def validate_po_id(cls, v):
        if v == "":
            return None
        return v


class InvoiceCreate(InvoiceBase):
    """Invoice create schema."""

    lines: list[InvoiceLineCreate]


class InvoiceUpdate(BaseSchema):
    """Invoice update schema."""

    supplier_name: Optional[str] = Field(None, max_length=255)
    po_id: Optional[str] = None
    due_date: Optional[date] = None
    total_amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    tax_amount: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    currency: Optional[str] = Field(None, max_length=3)
    status: Optional[DocumentStatusEnum] = None
    notes: Optional[str] = None
    metadata_: Optional[str] = None


class InvoiceResponse(InvoiceBase):
    """Invoice response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    status: DocumentStatusEnum
    lines: list[InvoiceLineResponse] = []
    created_at: datetime
    updated_at: datetime


# Delivery Note schemas
class DeliveryNoteLineBase(BaseSchema):
    """Delivery Note Line base schema."""

    line_number: int = Field(..., ge=1)
    product_code: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    quantity: Decimal = Field(..., gt=0, decimal_places=3)
    unit_price: Decimal = Field(..., ge=0, decimal_places=2)
    uom: str = Field(default="EA", max_length=20)


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Delivery Note Line create schema."""

    pass


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """Delivery Note Line response schema."""

    id: str
    delivery_note_id: str
    line_total: Decimal
    created_at: datetime
    updated_at: datetime


class DeliveryNoteBase(BaseSchema):
    """Delivery Note base schema."""

    dn_number: str = Field(..., max_length=100)
    supplier_id: str = Field(..., max_length=36)
    supplier_name: str = Field(..., max_length=255)
    po_id: Optional[str] = None
    delivery_date: date
    received_by: Optional[str] = Field(None, max_length=255)
    total_amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None
    metadata_: Optional[str] = None

    @field_validator("po_id")
    @classmethod
    def validate_po_id(cls, v):
        if v == "":
            return None
        return v


class DeliveryNoteCreate(DeliveryNoteBase):
    """Delivery Note create schema."""

    lines: list[DeliveryNoteLineCreate]


class DeliveryNoteUpdate(BaseSchema):
    """Delivery Note update schema."""

    supplier_name: Optional[str] = Field(None, max_length=255)
    po_id: Optional[str] = None
    received_by: Optional[str] = Field(None, max_length=255)
    total_amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    currency: Optional[str] = Field(None, max_length=3)
    status: Optional[DocumentStatusEnum] = None
    notes: Optional[str] = None
    metadata_: Optional[str] = None


class DeliveryNoteResponse(DeliveryNoteBase):
    """Delivery Note response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    status: DocumentStatusEnum
    lines: list[DeliveryNoteLineResponse] = []
    created_at: datetime
    updated_at: datetime

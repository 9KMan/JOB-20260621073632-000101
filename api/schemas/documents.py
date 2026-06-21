// api/schemas/documents.py
"""Document schemas for Purchase Orders, Invoices, and Delivery Notes."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


# ============== Purchase Order Schemas ==============

class POLineBase(BaseModel):
    """Base schema for PO line items."""
    line_number: int
    item_code: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    uom: str = Field(default="EA", max_length=20)


class POLineCreate(POLineBase):
    """Schema for creating a PO line item."""
    pass


class POLineResponse(POLineBase):
    """Schema for PO line item response."""
    id: UUID
    po_id: UUID
    line_amount: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PurchaseOrderBase(BaseModel):
    """Base schema for purchase orders."""
    po_number: str = Field(..., max_length=50)
    supplier_id: str = Field(..., max_length=100)
    supplier_name: str = Field(..., max_length=255)
    order_date: date
    expected_delivery_date: Optional[date] = None
    total_amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a purchase order."""
    lines: List[POLineCreate] = Field(..., min_length=1)


class PurchaseOrderUpdate(BaseModel):
    """Schema for updating a purchase order."""
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    expected_delivery_date: Optional[date] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    """Schema for purchase order response."""
    id: UUID
    status: str
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    lines: List[POLineResponse] = []

    model_config = {"from_attributes": True}


# ============== Invoice Schemas ==============

class InvoiceLineBase(BaseModel):
    """Base schema for invoice line items."""
    line_number: int
    item_code: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    uom: str = Field(default="EA", max_length=20)


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating an invoice line item."""
    pass


class InvoiceLineResponse(InvoiceLineBase):
    """Schema for invoice line item response."""
    id: UUID
    invoice_id: UUID
    line_amount: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InvoiceBase(BaseModel):
    """Base schema for invoices."""
    invoice_number: str = Field(..., max_length=50)
    supplier_id: str = Field(..., max_length=100)
    supplier_name: str = Field(..., max_length=255)
    invoice_date: date
    due_date: Optional[date] = None
    total_amount: Decimal = Field(..., gt=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    net_amount: Decimal = Field(..., ge=0)
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating an invoice."""
    po_id: Optional[UUID] = None
    lines: List[InvoiceLineCreate] = Field(..., min_length=1)


class InvoiceUpdate(BaseModel):
    """Schema for updating an invoice."""
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class InvoiceResponse(InvoiceBase):
    """Schema for invoice response."""
    id: UUID
    po_id: Optional[UUID] = None
    status: str
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    lines: List[InvoiceLineResponse] = []

    model_config = {"from_attributes": True}


# ============== Delivery Note Schemas ==============

class DeliveryNoteLineBase(BaseModel):
    """Base schema for delivery note line items."""
    line_number: int
    item_code: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    uom: str = Field(default="EA", max_length=20)


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating a delivery note line item."""
    pass


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """Schema for delivery note line item response."""
    id: UUID
    dn_id: UUID
    line_amount: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DeliveryNoteBase(BaseModel):
    """Base schema for delivery notes."""
    dn_number: str = Field(..., max_length=50)
    supplier_id: str = Field(..., max_length=100)
    supplier_name: str = Field(..., max_length=255)
    delivery_date: date
    received_date: Optional[date] = None
    total_amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating a delivery note."""
    po_id: Optional[UUID] = None
    lines: List[DeliveryNoteLineCreate] = Field(..., min_length=1)


class DeliveryNoteUpdate(BaseModel):
    """Schema for updating a delivery note."""
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    received_date: Optional[date] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class DeliveryNoteResponse(DeliveryNoteBase):
    """Schema for delivery note response."""
    id: UUID
    po_id: Optional[UUID] = None
    status: str
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    lines: List[DeliveryNoteLineResponse] = []

    model_config = {"from_attributes": True}


# ============== Document Lists ==============

class DocumentListResponse(BaseModel):
    """Schema for paginated document list response."""
    items: List
    total: int
    page: int
    page_size: int
    pages: int

// src/app/schemas/delivery_note.py
"""
Delivery Note schemas for API request/response validation.
"""
from datetime import date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.base import BaseSchema, TimestampSchema, PaginationParams, PaginatedResponse
from app.schemas.supplier import SupplierBrief
from app.schemas.purchase_order import PurchaseOrderBrief


# Line item schemas
class DeliveryNoteLineCreate(BaseSchema):
    """Schema for creating a DN line."""
    line_number: int = Field(..., ge=1)
    description: str = Field(..., min_length=1, max_length=500)
    sku: Optional[str] = Field(None, max_length=100)
    quantity: Decimal = Field(..., gt=0)
    unit_of_measure: str = Field(default="EA")
    condition: str = Field(default="good")
    notes: Optional[str] = None
    po_line_id: Optional[UUID] = None


class DeliveryNoteLineUpdate(BaseSchema):
    """Schema for updating a DN line."""
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    sku: Optional[str] = Field(None, max_length=100)
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit_of_measure: Optional[str] = None
    condition: Optional[str] = None
    notes: Optional[str] = None


class DeliveryNoteLineResponse(BaseSchema):
    """DN line response schema."""
    id: UUID
    line_number: int
    description: str
    sku: Optional[str]
    quantity: Decimal
    unit_of_measure: str
    condition: str
    notes: Optional[str]
    po_line_id: Optional[UUID]


# Header schemas
class DeliveryNoteCreate(BaseSchema):
    """Schema for creating a delivery note."""
    dn_number: str = Field(..., min_length=1, max_length=50)
    supplier_id: UUID
    po_id: Optional[UUID] = None
    received_date: date
    received_by: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    lines: List[DeliveryNoteLineCreate]


class DeliveryNoteUpdate(BaseSchema):
    """Schema for updating a delivery note."""
    po_id: Optional[UUID] = None
    received_date: Optional[date] = None
    received_by: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = None
    notes: Optional[str] = None


class DeliveryNoteResponse(TimestampSchema):
    """Delivery note response schema."""
    id: UUID
    dn_number: str
    supplier_id: UUID
    po_id: Optional[UUID]
    received_date: date
    received_by: Optional[str]
    status: str
    notes: Optional[str]
    lines: List[DeliveryNoteLineResponse] = []
    supplier: Optional[SupplierBrief] = None
    purchase_order: Optional[PurchaseOrderBrief] = None


class DeliveryNoteBrief(BaseSchema):
    """Brief delivery note information."""
    id: UUID
    dn_number: str
    received_date: date
    status: str


class DeliveryNoteListResponse(PaginatedResponse[DeliveryNoteResponse]):
    """Paginated DN list response."""
    pass

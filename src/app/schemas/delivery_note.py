// src/app/schemas/delivery_note.py
"""
Delivery Note schemas.
"""
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field

from app.schemas.common import BaseSchema, TimestampMixin
from app.schemas.supplier import SupplierResponse


class DeliveryNoteLineBase(BaseModel):
    """Base DN line schema."""
    line_number: int = Field(..., ge=1)
    product_code: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    accepted_quantity: Optional[Decimal] = Field(default=None, ge=0)
    rejected_quantity: Optional[Decimal] = Field(default=None, ge=0)


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """DN line creation schema."""
    pass


class DeliveryNoteLineResponse(DeliveryNoteLineBase, TimestampMixin):
    """DN line response schema."""
    id: str
    delivery_note_id: str
    net_quantity: Decimal


class DeliveryNoteBase(BaseModel):
    """Base DN schema."""
    dn_number: str = Field(..., min_length=1, max_length=50)
    supplier_id: str
    po_reference: Optional[str] = Field(default=None, max_length=50)
    delivery_date: date
    received_by: Optional[str] = Field(default=None, max_length=255)
    notes: Optional[str] = None
    erp_reference: Optional[str] = Field(default=None, max_length=100)


class DeliveryNoteCreate(DeliveryNoteBase):
    """DN creation schema."""
    lines: List[DeliveryNoteLineCreate]


class DeliveryNoteUpdate(BaseModel):
    """DN update schema."""
    dn_number: Optional[str] = Field(default=None, min_length=1, max_length=50)
    supplier_id: Optional[str] = None
    po_reference: Optional[str] = Field(default=None, max_length=50)
    delivery_date: Optional[date] = None
    status: Optional[str] = None
    received_by: Optional[str] = Field(default=None, max_length=255)
    notes: Optional[str] = None
    erp_reference: Optional[str] = Field(default=None, max_length=100)


class DeliveryNoteResponse(DeliveryNoteBase, TimestampMixin):
    """DN response schema."""
    id: str
    status: str
    supplier: Optional[SupplierResponse] = None
    lines: List[DeliveryNoteLineResponse] = []
    total_quantity: Decimal

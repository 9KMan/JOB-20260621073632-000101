// src/schemas/delivery_note.py
"""Delivery Note schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.base import BaseSchema


class DeliveryNoteLineBase(BaseSchema):
    """Base delivery note line schema."""
    line_number: int
    item_code: Optional[str] = None
    item_description: str
    quantity: Decimal
    unit_of_measure: str = "EA"
    unit_price: Decimal
    line_total: Decimal
    po_line_id: Optional[str] = None
    match_score: Optional[Decimal] = None
    status: str = "pending"


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Delivery note line creation schema."""
    pass


class DeliveryNoteLineUpdate(BaseSchema):
    """Delivery note line update schema."""
    item_code: Optional[str] = None
    item_description: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit_of_measure: Optional[str] = None
    unit_price: Optional[Decimal] = None
    po_line_id: Optional[str] = None
    status: Optional[str] = None


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """Delivery note line response schema."""
    id: str
    delivery_note_id: str
    created_at: datetime
    updated_at: datetime


class DeliveryNoteBase(BaseSchema):
    """Base delivery note schema."""
    dn_number: str
    supplier_id: str
    supplier_name: str
    supplier_code: Optional[str] = None
    po_id: Optional[str] = None
    po_number: Optional[str] = None
    dn_date: date
    delivery_date: Optional[date] = None
    receipt_date: Optional[datetime] = None
    status: str = "pending"
    currency: str = "USD"
    notes: Optional[str] = None
    delivery_address: Optional[str] = None
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Delivery note creation schema."""
    subtotal: Decimal = Decimal("0.00")
    tax_amount: Decimal = Decimal("0.00")
    total_amount: Decimal
    lines: List[DeliveryNoteLineCreate] = Field(default_factory=list)


class DeliveryNoteUpdate(BaseSchema):
    """Delivery note update schema."""
    supplier_name: Optional[str] = None
    supplier_code: Optional[str] = None
    po_id: Optional[str] = None
    po_number: Optional[str] = None
    delivery_date: Optional[date] = None
    receipt_date: Optional[datetime] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    delivery_address: Optional[str] = None
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    received_by: Optional[str] = None
    matched_by: Optional[str] = None


class DeliveryNoteResponse(DeliveryNoteBase):
    """Delivery note response schema."""
    id: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    match_score: Optional[Decimal] = None
    match_status: Optional[str] = None
    received_by: Optional[str] = None
    matched_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    lines: List[DeliveryNoteLineResponse] = Field(default_factory=list)

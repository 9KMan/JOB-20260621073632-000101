// src/app/schemas/delivery_note.py
"""Delivery Note schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DeliveryNoteLineBase(BaseModel):
    """Base delivery note line schema."""
    
    line_number: int = Field(ge=1)
    product_code: str = Field(max_length=100)
    product_name: str = Field(max_length=255)
    description: Optional[str] = None
    quantity_ordered: Decimal = Field(ge=0, decimal_places=3)
    quantity_delivered: Decimal = Field(ge=0, decimal_places=3)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Optional[Decimal] = Field(default=None, ge=0, decimal_places=4)
    notes: Optional[str] = None


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Delivery note line creation schema."""
    pass


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """Delivery note line response schema."""
    
    id: str
    delivery_note_id: str
    line_amount: Decimal
    po_line_id: Optional[str] = None
    invoice_line_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DeliveryNoteBase(BaseModel):
    """Base delivery note schema."""
    
    dn_number: str = Field(max_length=50)
    supplier_id: str
    supplier_name: str = Field(max_length=255)
    supplier_code: str = Field(max_length=50)
    dn_date: date
    received_date: Optional[date] = None
    po_reference: Optional[str] = None
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Delivery note creation schema."""
    
    lines: list[DeliveryNoteLineCreate] = Field(min_length=1)
    status: Optional[str] = "draft"


class DeliveryNoteUpdate(BaseModel):
    """Delivery note update schema."""
    
    supplier_name: Optional[str] = None
    supplier_code: Optional[str] = None
    received_date: Optional[date] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class DeliveryNoteResponse(DeliveryNoteBase):
    """Delivery note response schema."""
    
    id: str
    po_id: Optional[str] = None
    total_amount: Decimal
    status: str
    is_archived: bool
    lines: list[DeliveryNoteLineResponse] = []
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DeliveryNoteListResponse(BaseModel):
    """Delivery note list response with pagination."""
    
    delivery_notes: list[DeliveryNoteResponse]
    total: int
    page: int
    page_size: int


class DeliveryNoteSummary(BaseModel):
    """Delivery note summary for matching."""
    
    id: str
    dn_number: str
    supplier_code: str
    total_amount: Decimal
    currency: str
    status: str
    open_amount: Decimal
    line_count: int
    
    model_config = ConfigDict(from_attributes=True)

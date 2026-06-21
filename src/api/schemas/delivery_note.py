// src/api/schemas/delivery_note.py
from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from src.models.delivery_note import DeliveryNoteStatus


class DeliveryNoteLineBase(BaseModel):
    """Base DN line schema."""
    line_number: int
    item_code: Optional[str] = None
    description: str = Field(..., max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_of_measure: str = "EA"
    unit_price: Decimal = Field(..., ge=0)
    tax_rate: Decimal = Field(default=Decimal("0"), ge=0, le=1)


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """DN line creation schema."""
    matched_po_line_id: Optional[UUID] = None


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """DN line response schema."""
    id: UUID
    line_total: Decimal
    tax_amount: Decimal
    matched_po_line_id: Optional[UUID] = None
    
    class Config:
        from_attributes = True


class DeliveryNoteBase(BaseModel):
    """Base DN schema."""
    dn_number: str = Field(..., max_length=100)
    supplier_id: UUID
    supplier_name: str = Field(..., max_length=255)
    supplier_code: Optional[str] = None
    delivery_date: date
    received_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None
    carrier_info: Optional[str] = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """DN creation schema."""
    line_items: List[DeliveryNoteLineCreate] = Field(default_factory=list)


class DeliveryNoteUpdate(BaseModel):
    """DN update schema."""
    supplier_name: Optional[str] = None
    supplier_code: Optional[str] = None
    received_date: Optional[date] = None
    status: Optional[DeliveryNoteStatus] = None
    notes: Optional[str] = None
    carrier_info: Optional[str] = None


class DeliveryNoteResponse(DeliveryNoteBase):
    """DN response schema."""
    id: UUID
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    status: DeliveryNoteStatus
    matched_po_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    line_items: List[DeliveryNoteLineResponse] = []
    
    class Config:
        from_attributes = True


class DeliveryNoteListResponse(BaseModel):
    """DN list response schema."""
    items: List[DeliveryNoteResponse]
    total: int
    page: int
    page_size: int

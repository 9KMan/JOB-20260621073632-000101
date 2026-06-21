// src/api/schemas/delivery_note.py
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from datetime import date
from src.models.delivery_note import DeliveryNoteStatus


class DeliveryNoteLineBase(BaseModel):
    line_number: int
    product_code: Optional[str] = None
    description: str
    quantity: Decimal
    unit_of_measure: str = "EA"


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    pass


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    id: UUID
    line_total: Decimal
    
    class Config:
        from_attributes = True


class DeliveryNoteBase(BaseModel):
    dn_number: str
    supplier_code: str
    supplier_name: str
    delivery_date: date
    purchase_order_id: Optional[UUID] = None
    received_by: Optional[str] = None
    currency: str = "USD"
    notes: Optional[str] = None


class DeliveryNoteCreate(DeliveryNoteBase):
    lines: List[DeliveryNoteLineCreate]


class DeliveryNoteUpdate(BaseModel):
    supplier_code: Optional[str] = None
    supplier_name: Optional[str] = None
    status: Optional[DeliveryNoteStatus] = None
    received_by: Optional[str] = None
    notes: Optional[str] = None


class DeliveryNoteResponse(DeliveryNoteBase):
    id: UUID
    status: DeliveryNoteStatus
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    created_at: date
    updated_at: date
    lines: List[DeliveryNoteLineResponse] = []
    
    class Config:
        from_attributes = True

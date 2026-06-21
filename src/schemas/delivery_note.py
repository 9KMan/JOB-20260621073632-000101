// src/schemas/delivery_note.py
"""
Delivery Note Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal

from src.schemas.common import TimestampMixin, UUIDMixin


class DeliveryNoteLineBase(BaseModel):
    """Base schema for Delivery Note line items"""
    line_number: int
    item_code: Optional[str] = None
    description: str = Field(..., max_length=500)
    ordered_quantity: Decimal = Field(default=Decimal("0"), ge=0)
    delivered_quantity: Decimal = Field(..., ge=0)
    accepted_quantity: Decimal = Field(default=Decimal("0"), ge=0)
    rejected_quantity: Decimal = Field(default=Decimal("0"), ge=0)
    unit_of_measure: str = "EA"
    purchase_order_line_id: Optional[UUID] = None


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating Delivery Note line items"""
    pass


class DeliveryNoteLineResponse(DeliveryNoteLineBase, UUIDMixin):
    """Response schema for Delivery Note line items"""
    
    class Config:
        from_attributes = True


class DeliveryNoteBase(BaseModel):
    """Base schema for Delivery Note"""
    dn_number: str = Field(..., max_length=50)
    supplier_id: UUID
    supplier_name: str = Field(..., max_length=255)
    supplier_code: Optional[str] = None
    dn_date: datetime
    received_date: Optional[datetime] = None
    currency: str = Field(default="USD", max_length=3)
    received_by: Optional[str] = None
    warehouse_location: Optional[str] = None
    notes: Optional[str] = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating a Delivery Note"""
    line_items: List[DeliveryNoteLineCreate] = Field(default_factory=list)


class DeliveryNoteUpdate(BaseModel):
    """Schema for updating a Delivery Note"""
    supplier_name: Optional[str] = None
    supplier_code: Optional[str] = None
    received_date: Optional[datetime] = None
    status: Optional[str] = None
    received_by: Optional[str] = None
    warehouse_location: Optional[str] = None
    notes: Optional[str] = None


class DeliveryNoteResponse(DeliveryNoteBase, UUIDMixin, TimestampMixin):
    """Response schema for Delivery Note"""
    purchase_order_id: Optional[UUID] = None
    invoice_id: Optional[UUID] = None
    subtotal: Decimal
    total_amount: Decimal
    status: str
    created_by: Optional[UUID] = None
    line_items: List[DeliveryNoteLineResponse] = []
    
    class Config:
        from_attributes = True


class DeliveryNoteListResponse(BaseModel):
    """Response schema for listing Delivery Notes"""
    items: List[DeliveryNoteResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

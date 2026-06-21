# src/schemas/delivery_note.py
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field

from src.schemas.common import TimestampMixinSchema, UUIDMixinSchema


# Line Items
class DeliveryNoteLineItemBase(BaseModel):
    """Base schema for delivery note line items."""
    line_number: int = Field(ge=1)
    item_code: str = Field(max_length=100)
    description: str = Field(max_length=500)
    quantity_delivered: Decimal = Field(ge=0)
    unit_price: Decimal = Field(ge=0)
    line_total: Decimal = Field(ge=0)


class DeliveryNoteLineItemCreate(DeliveryNoteLineItemBase):
    """Schema for creating delivery note line items."""
    pass


class DeliveryNoteLineItemResponse(DeliveryNoteLineItemBase, UUIDMixinSchema):
    """Schema for delivery note line item response."""
    delivery_note_id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


# Delivery Note
class DeliveryNoteBase(BaseModel):
    """Base schema for Delivery Notes."""
    dn_number: str = Field(max_length=50)
    supplier_id: str = Field(max_length=100)
    supplier_name: str = Field(max_length=255)
    delivery_date: date
    subtotal: Decimal = Field(ge=0)
    total_amount: Decimal = Field(ge=0)
    currency: str = Field(default="USD", max_length=3)
    status: str = Field(default="RECEIVED", max_length=20)
    notes: Optional[str] = None
    purchase_order_id: Optional[str] = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating Delivery Notes."""
    line_items: List[DeliveryNoteLineItemCreate] = []


class DeliveryNoteUpdate(BaseModel):
    """Schema for updating Delivery Notes."""
    supplier_name: Optional[str] = None
    delivery_date: Optional[date] = None
    subtotal: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    purchase_order_id: Optional[str] = None


class DeliveryNoteResponse(DeliveryNoteBase, UUIDMixinSchema, TimestampMixinSchema):
    """Schema for Delivery Note response."""
    line_items: List[DeliveryNoteLineItemResponse] = []
    
    model_config = {"from_attributes": True}

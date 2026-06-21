// src/schemas/delivery_note.py
"""
FinaRo AP Automation Core Engine
Delivery Note Pydantic Schemas
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.base import BaseSchema


class DeliveryNoteLineBase(BaseSchema):
    """Base schema for Delivery Note Line."""
    line_number: int = Field(..., ge=1)
    internal_reference: Optional[str] = None
    product_id: Optional[UUID] = None
    product_code: Optional[str] = None
    product_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    quantity_delivered: Decimal = Field(..., ge=Decimal('0'))
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Optional[Decimal] = Field(None, ge=Decimal('0'))
    quality_status: str = Field(default="PENDING")


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating a Delivery Note Line."""
    pass


class DeliveryNoteLineUpdate(BaseSchema):
    """Schema for updating a Delivery Note Line."""
    line_number: Optional[int] = Field(None, ge=1)
    internal_reference: Optional[str] = None
    product_id: Optional[UUID] = None
    product_code: Optional[str] = None
    product_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    quantity_delivered: Optional[Decimal] = Field(None, ge=Decimal('0'))
    quantity_received: Optional[Decimal] = Field(None, ge=Decimal('0'))
    quantity_rejected: Optional[Decimal] = Field(None, ge=Decimal('0'))
    quantity_returned: Optional[Decimal] = Field(None, ge=Decimal('0'))
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    unit_price: Optional[Decimal] = Field(None, ge=Decimal('0'))
    quality_status: Optional[str] = None
    quantity_matched: Optional[Decimal] = Field(None, ge=Decimal('0'))
    status: Optional[str] = None


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """Schema for Delivery Note Line response."""
    id: UUID
    dn_id: UUID
    quantity_received: Decimal
    quantity_rejected: Decimal
    quantity_returned: Decimal
    quantity_matched: Decimal
    quantity_unmatched: Decimal
    line_total: Optional[Decimal]
    quality_status: str
    status: str
    created_at: datetime
    updated_at: datetime


class DeliveryNoteBase(BaseSchema):
    """Base schema for Delivery Note."""
    dn_number: str = Field(..., min_length=1, max_length=50)
    supplier_id: UUID
    supplier_name: str = Field(..., min_length=1, max_length=255)
    supplier_code: Optional[str] = None
    po_id: Optional[UUID] = None
    supplier_dn_number: Optional[str] = None
    dn_date: date
    received_date: Optional[date] = None
    goods_receipt_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    total_amount: Decimal = Field(default=Decimal('0'))
    carrier_name: Optional[str] = None
    tracking_number: Optional[str] = None
    vehicle_number: Optional[str] = None
    notes: Optional[str] = None
    inspection_notes: Optional[str] = None
    department: Optional[str] = None
    received_by: Optional[str] = None
    warehouse_location: Optional[str] = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating a Delivery Note."""
    lines: List[DeliveryNoteLineCreate] = Field(default_factory=list)


class DeliveryNoteUpdate(BaseSchema):
    """Schema for updating a Delivery Note."""
    dn_number: Optional[str] = Field(None, min_length=1, max_length=50)
    supplier_id: Optional[UUID] = None
    supplier_name: Optional[str] = Field(None, min_length=1, max_length=255)
    supplier_code: Optional[str] = None
    po_id: Optional[UUID] = None
    supplier_dn_number: Optional[str] = None
    dn_date: Optional[date] = None
    received_date: Optional[date] = None
    goods_receipt_date: Optional[date] = None
    status: Optional[str] = None
    currency: Optional[str] = Field(None, max_length=3)
    total_amount: Optional[Decimal] = None
    carrier_name: Optional[str] = None
    tracking_number: Optional[str] = None
    vehicle_number: Optional[str] = None
    notes: Optional[str] = None
    inspection_notes: Optional[str] = None
    department: Optional[str] = None
    received_by: Optional[str] = None
    warehouse_location: Optional[str] = None


class DeliveryNoteResponse(DeliveryNoteBase):
    """Schema for Delivery Note response."""
    id: UUID
    status: str
    is_received: bool
    lines: List[DeliveryNoteLineResponse]
    created_at: datetime
    updated_at: datetime
    
    @field_validator('lines', mode='before')
    @classmethod
    def validate_lines(cls, v):
        if v is None:
            return []
        return v


class DeliveryNoteListResponse(BaseSchema):
    """Schema for Delivery Note list item response."""
    id: UUID
    dn_number: str
    supplier_id: UUID
    supplier_name: str
    dn_date: date
    received_date: Optional[date]
    status: str
    total_amount: Decimal
    carrier_name: Optional[str]
    tracking_number: Optional[str]
    department: Optional[str]
    created_at: datetime

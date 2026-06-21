// api/schemas/delivery_note.py
"""Delivery Note Pydantic schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# Line schemas
class DeliveryNoteLineBase(BaseModel):
    """Base schema for Delivery Note line items."""
    
    line_number: int = Field(ge=1)
    item_code: Optional[str] = Field(None, max_length=50)
    item_description: str = Field(max_length=500)
    quantity_delivered: Decimal = Field(ge=0)
    unit_price: Decimal = Field(ge=0)


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating a Delivery Note line item."""
    
    quantity_accepted: Optional[Decimal] = Field(None, ge=0)
    matched_po_line_id: Optional[UUID] = None


class DeliveryNoteLineUpdate(BaseModel):
    """Schema for updating a Delivery Note line item."""
    
    item_code: Optional[str] = Field(None, max_length=50)
    item_description: Optional[str] = Field(None, max_length=500)
    quantity_delivered: Optional[Decimal] = Field(None, ge=0)
    quantity_accepted: Optional[Decimal] = Field(None, ge=0)
    quantity_rejected: Optional[Decimal] = Field(None, ge=0)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    matched_po_line_id: Optional[UUID] = None
    match_confidence: Optional[Decimal] = Field(None, ge=0, le=1)
    notes: Optional[str] = None


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """Schema for Delivery Note line item response."""
    
    id: UUID
    delivery_note_id: UUID
    quantity_accepted: Optional[Decimal] = None
    quantity_rejected: Decimal
    line_total: Decimal
    matched_po_line_id: Optional[UUID] = None
    match_confidence: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


# Delivery Note schemas
class DeliveryNoteBase(BaseModel):
    """Base schema for Delivery Notes."""
    
    dn_number: str = Field(max_length=50)
    supplier_id: UUID
    supplier_name: str = Field(max_length=255)
    supplier_code: Optional[str] = Field(None, max_length=50)
    po_reference: Optional[str] = Field(None, max_length=50)
    delivery_date: date
    received_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    carrier: Optional[str] = Field(None, max_length=100)
    tracking_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    metadata: Optional[dict] = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating a Delivery Note."""
    
    lines: List[DeliveryNoteLineCreate] = Field(default_factory=list)
    
    @field_validator("dn_number")
    @classmethod
    def validate_dn_number(cls, v: str) -> str:
        return v.strip().upper()


class DeliveryNoteUpdate(BaseModel):
    """Schema for updating a Delivery Note."""
    
    supplier_name: Optional[str] = Field(None, max_length=255)
    supplier_code: Optional[str] = Field(None, max_length=50)
    received_date: Optional[date] = None
    status: Optional[str] = None
    carrier: Optional[str] = Field(None, max_length=100)
    tracking_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    metadata: Optional[dict] = None
    is_matched: Optional[bool] = None


class DeliveryNoteResponse(DeliveryNoteBase):
    """Schema for Delivery Note response."""
    
    id: UUID
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    status: str
    is_matched: bool
    matched_at: Optional[datetime] = None
    line_count: int
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class DeliveryNoteDetailResponse(DeliveryNoteResponse):
    """Schema for detailed Delivery Note response with lines."""
    
    lines: List[DeliveryNoteLineResponse] = []
    
    model_config = {"from_attributes": True}


class DeliveryNoteListResponse(BaseModel):
    """Schema for paginated list of Delivery Notes."""
    
    items: List[DeliveryNoteResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

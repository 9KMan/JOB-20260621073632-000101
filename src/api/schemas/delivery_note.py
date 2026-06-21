// src/api/schemas/delivery_note.py
"""Delivery Note schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DeliveryNoteLineBase(BaseModel):
    """Base DN line schema."""
    line_number: int = Field(ge=1)
    item_code: Optional[str] = Field(default=None, max_length=50)
    description: str = Field(min_length=1, max_length=500)
    quantity_received: Decimal = Field(gt=0, decimal_places=3)
    quantity_accepted: Decimal = Field(ge=0, decimal_places=3)
    unit_of_measure: Optional[str] = Field(default=None, max_length=20)
    unit_price: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2)
    
    @field_validator("quantity_accepted")
    @classmethod
    def validate_quantity(cls, v, info):
        """Validate accepted quantity doesn't exceed received."""
        if "quantity_received" in info.data:
            if v > info.data["quantity_received"]:
                raise ValueError("Accepted quantity cannot exceed received quantity")
        return v


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """DN line creation schema."""
    line_amount: Optional[Decimal] = Field(default=None, ge=0)
    
    def calculate_amounts(self) -> tuple[Decimal, Decimal]:
        """Calculate line amount."""
        if self.unit_price:
            return self.quantity_accepted * self.unit_price, Decimal("0")
        return Decimal("0"), Decimal("0")


class DeliveryNoteLineUpdate(BaseModel):
    """DN line update schema."""
    item_code: Optional[str] = None
    description: Optional[str] = None
    quantity_received: Optional[Decimal] = None
    quantity_accepted: Optional[Decimal] = None
    unit_of_measure: Optional[str] = None
    unit_price: Optional[Decimal] = None


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """DN line response schema."""
    id: UUID
    delivery_note_id: UUID
    line_amount: Decimal
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class DeliveryNoteBase(BaseModel):
    """Base DN schema."""
    dn_number: str = Field(min_length=1, max_length=50)
    supplier_id: UUID
    po_id: Optional[UUID] = None
    delivery_date: date
    currency: str = Field(default="USD", min_length=3, max_length=3)
    notes: Optional[str] = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """DN creation schema."""
    lines: List[DeliveryNoteLineCreate] = Field(min_length=1)
    total_amount: Optional[Decimal] = None
    
    def calculate_total(self) -> Decimal:
        """Calculate total amount from lines."""
        total = Decimal("0")
        for line in self.lines:
            if line.unit_price:
                total += line.quantity_accepted * line.unit_price
        return total


class DeliveryNoteUpdate(BaseModel):
    """DN update schema."""
    supplier_id: Optional[UUID] = None
    po_id: Optional[UUID] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class DeliveryNoteResponse(DeliveryNoteBase):
    """DN response schema."""
    id: UUID
    status: str
    total_amount: Decimal
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    lines: List[DeliveryNoteLineResponse] = []
    
    model_config = {"from_attributes": True}


class DeliveryNoteListResponse(BaseModel):
    """DN list response schema."""
    items: List[DeliveryNoteResponse]
    total: int
    page: int
    size: int
    pages: int

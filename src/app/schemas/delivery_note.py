# src/app/schemas/delivery_note.py
"""Delivery Note schemas."""
import uuid
import decimal
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict

from src.app.schemas.base import BaseSchema
from src.app.schemas.supplier import SupplierResponse


class DeliveryNoteLineBase(BaseSchema):
    """Base DN line schema."""
    
    line_number: int = Field(..., ge=1)
    purchase_order_line_id: Optional[uuid.UUID] = None
    item_code: Optional[str] = Field(None, max_length=50)
    item_description: str = Field(..., min_length=1, max_length=500)
    quantity: decimal.Decimal = Field(..., gt=0)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    unit_price: decimal.Decimal = Field(..., ge=0)
    tax_rate: decimal.Decimal = Field(default=decimal.Decimal("0.0000"), ge=0)


class DeliveryNoteLineCreate(DeliveryNoteLineBase):
    """Schema for creating a DN line."""
    
    pass


class DeliveryNoteLineUpdate(BaseSchema):
    """Schema for updating a DN line."""
    
    purchase_order_line_id: Optional[uuid.UUID] = None
    item_code: Optional[str] = Field(None, max_length=50)
    item_description: Optional[str] = Field(None, min_length=1, max_length=500)
    quantity: Optional[decimal.Decimal] = Field(None, gt=0)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    unit_price: Optional[decimal.Decimal] = Field(None, ge=0)
    tax_rate: Optional[decimal.Decimal] = Field(None, ge=0)


class DeliveryNoteLineResponse(DeliveryNoteLineBase):
    """Schema for DN line response."""
    
    id: uuid.UUID
    delivery_note_id: uuid.UUID
    line_total: decimal.Decimal
    tax_amount: decimal.Decimal
    created_at: datetime
    updated_at: datetime


class DeliveryNoteBase(BaseSchema):
    """Base DN schema."""
    
    dn_number: str = Field(..., min_length=1, max_length=50)
    supplier_id: uuid.UUID
    purchase_order_id: Optional[uuid.UUID] = None
    invoice_id: Optional[uuid.UUID] = None
    status: str = Field(default="DRAFT")
    delivery_date: datetime
    received_date: Optional[datetime] = None
    currency: str = Field(default="USD", max_length=3)
    notes: Optional[str] = None


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating a DN."""
    
    lines: List[DeliveryNoteLineCreate] = Field(default_factory=list)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "dn_number": "DN-2024-001",
                "supplier_id": "550e8400-e29b-41d4-a716-446655440000",
                "purchase_order_id": "660e8400-e29b-41d4-a716-446655440001",
                "status": "DRAFT",
                "delivery_date": "2024-01-25T00:00:00Z",
                "received_date": "2024-01-26T00:00:00Z",
                "currency": "USD",
                "notes": "Delivered on time",
                "lines": [
                    {
                        "line_number": 1,
                        "purchase_order_line_id": "770e8400-e29b-41d4-a716-446655440002",
                        "item_code": "ITEM001",
                        "item_description": "Widget A",
                        "quantity": 100,
                        "unit_of_measure": "EA",
                        "unit_price": 25.00,
                        "tax_rate": 0.10,
                    }
                ],
            }
        }
    )


class DeliveryNoteUpdate(BaseSchema):
    """Schema for updating a DN."""
    
    dn_number: Optional[str] = Field(None, min_length=1, max_length=50)
    supplier_id: Optional[uuid.UUID] = None
    purchase_order_id: Optional[uuid.UUID] = None
    invoice_id: Optional[uuid.UUID] = None
    status: Optional[str] = None
    delivery_date: Optional[datetime] = None
    received_date: Optional[datetime] = None
    currency: Optional[str] = Field(None, max_length=3)
    notes: Optional[str] = None
    is_archived: Optional[bool] = None


class DeliveryNoteResponse(DeliveryNoteBase):
    """Schema for DN response."""
    
    id: uuid.UUID
    subtotal: decimal.Decimal
    tax_amount: decimal.Decimal
    total_amount: decimal.Decimal
    is_archived: bool
    created_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    supplier: Optional[SupplierResponse] = None
    lines: List[DeliveryNoteLineResponse] = Field(default_factory=list)


class DeliveryNoteListResponse(BaseSchema):
    """Schema for paginated DN list response."""
    
    items: list[DeliveryNoteResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool

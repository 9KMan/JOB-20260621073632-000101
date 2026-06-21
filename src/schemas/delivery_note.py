# src/schemas/delivery_note.py
"""Delivery Note Pydantic schemas."""
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from datetime import date

from pydantic import BaseModel, Field


# Line Items
class DeliveryNoteLineItemBase(BaseModel):
    """Base schema for delivery note line items."""
    
    line_number: str = Field(..., max_length=10, description="Line number")
    sku: Optional[str] = Field(None, max_length=100, description="SKU code")
    description: str = Field(..., max_length=500, description="Item description")
    quantity_delivered: Decimal = Field(..., gt=0, description="Delivered quantity")
    quantity_accepted: Decimal = Field(default=Decimal("0.00"), ge=0, description="Accepted quantity")
    quantity_rejected: Decimal = Field(default=Decimal("0.00"), ge=0, description="Rejected quantity")
    unit_of_measure: str = Field(default="EA", max_length=20, description="Unit of measure")
    unit_price: Decimal = Field(..., gt=0, description="Unit price")


class DeliveryNoteLineItemCreate(DeliveryNoteLineItemBase):
    """Schema for creating delivery note line items."""
    pass


class DeliveryNoteLineItemResponse(DeliveryNoteLineItemBase):
    """Schema for delivery note line item response."""
    
    id: UUID
    delivery_note_id: UUID
    line_total: Decimal
    created_at: str
    updated_at: str
    
    model_config = {"from_attributes": True}


# Delivery Note
class DeliveryNoteBase(BaseModel):
    """Base schema for delivery notes."""
    
    dn_number: str = Field(..., max_length=50, description="Delivery note number")
    supplier_id: str = Field(..., max_length=50, description="Supplier ID")
    supplier_name: str = Field(..., max_length=255, description="Supplier name")
    supplier_code: Optional[str] = Field(None, max_length=50, description="Supplier code")
    po_reference: Optional[str] = Field(None, max_length=50, description="PO reference")
    invoice_reference: Optional[str] = Field(None, max_length=50, description="Invoice reference")
    delivery_date: date = Field(..., description="Delivery date")
    currency: str = Field(default="USD", max_length=3, description="Currency code")
    total_amount: Decimal = Field(..., ge=0, description="Total amount")
    notes: Optional[str] = Field(None, description="Notes")
    carrier_name: Optional[str] = Field(None, max_length=255, description="Carrier name")
    tracking_number: Optional[str] = Field(None, max_length=100, description="Tracking number")


class DeliveryNoteCreate(DeliveryNoteBase):
    """Schema for creating delivery notes."""
    
    line_items: List[DeliveryNoteLineItemCreate] = Field(
        default_factory=list,
        description="Line items"
    )


class DeliveryNoteUpdate(BaseModel):
    """Schema for updating delivery notes."""
    
    supplier_name: Optional[str] = Field(None, max_length=255, description="Supplier name")
    supplier_code: Optional[str] = Field(None, max_length=50, description="Supplier code")
    po_reference: Optional[str] = Field(None, max_length=50, description="PO reference")
    invoice_reference: Optional[str] = Field(None, max_length=50, description="Invoice reference")
    total_amount: Optional[Decimal] = Field(None, ge=0, description="Total amount")
    status: Optional[str] = Field(None, description="DN status")
    notes: Optional[str] = Field(None, description="Notes")
    carrier_name: Optional[str] = Field(None, max_length=255, description="Carrier name")
    tracking_number: Optional[str] = Field(None, max_length=100, description="Tracking number")
    line_items: Optional[List[DeliveryNoteLineItemCreate]] = Field(
        None,
        description="Line items"
    )


class DeliveryNoteResponse(DeliveryNoteBase):
    """Schema for delivery note response."""
    
    id: UUID
    status: str
    is_deleted: str
    created_at: str
    updated_at: str
    line_items: List[DeliveryNoteLineItemResponse] = []
    
    model_config = {"from_attributes": True}


class DeliveryNoteListResponse(BaseModel):
    """Schema for delivery note list response."""
    
    id: UUID
    dn_number: str
    supplier_name: str
    delivery_date: date
    total_amount: Decimal
    status: str
    created_at: str
    
    model_config = {"from_attributes": True}

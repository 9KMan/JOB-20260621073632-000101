// api/schemas/supplier.py
"""Supplier schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SupplierBase(BaseModel):
    """Base supplier schema."""
    
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    tax_id: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)
    payment_terms_days: Optional[str] = Field(None, max_length=100)


class SupplierCreate(SupplierBase):
    """Schema for creating a supplier."""
    pass


class SupplierUpdate(BaseModel):
    """Schema for updating a supplier."""
    
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    tax_id: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    payment_terms_days: Optional[str] = Field(None, max_length=100)


class SupplierResponse(SupplierBase):
    """Schema for supplier response."""
    
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}

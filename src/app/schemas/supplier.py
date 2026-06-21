// src/app/schemas/supplier.py
"""Supplier Pydantic schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class SupplierBase(BaseModel):
    """Base supplier schema."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    tax_id: Optional[str] = Field(None, max_length=50)
    payment_terms: str = Field(default="Net 30", max_length=100)


class SupplierCreate(SupplierBase):
    """Supplier creation schema."""
    is_active: bool = True


class SupplierUpdate(BaseModel):
    """Supplier update schema."""
    name: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    tax_id: Optional[str] = Field(None, max_length=50)
    payment_terms: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class SupplierResponse(SupplierBase):
    """Supplier response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

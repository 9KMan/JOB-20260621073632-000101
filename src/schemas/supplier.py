// src/schemas/supplier.py
"""Supplier schemas."""
from typing import Optional
from pydantic import Field, EmailStr

from src.schemas.base import BaseSchema, TimestampUUIDSchema


class SupplierBase(BaseSchema):
    """Base supplier schema."""
    
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    tax_id: Optional[str] = Field(None, max_length=50)


class SupplierCreate(SupplierBase):
    """Schema for creating a supplier."""
    
    is_active: bool = True


class SupplierUpdate(BaseSchema):
    """Schema for updating a supplier."""
    
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    tax_id: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class SupplierResponse(TimestampUUIDSchema):
    """Schema for supplier response."""
    
    code: str
    name: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None
    is_active: bool

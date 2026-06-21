// src/schemas/supplier.py
"""Supplier schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class SupplierBase(BaseModel):
    """Base supplier schema."""
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    tax_id: Optional[str] = Field(None, max_length=50)
    is_active: bool = True


class SupplierCreate(SupplierBase):
    """Schema for supplier creation."""
    pass


class SupplierUpdate(BaseModel):
    """Schema for supplier update."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    tax_id: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class SupplierResponse(SupplierBase):
    """Schema for supplier response."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class SupplierListResponse(BaseModel):
    """Schema for paginated supplier list."""
    items: list[SupplierResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

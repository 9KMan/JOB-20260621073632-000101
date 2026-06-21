// src/schemas/supplier.py
"""Supplier schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field, ConfigDict, EmailStr

from src.schemas.common import BaseSchema


class SupplierBase(BaseSchema):
    """Base supplier schema."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    tax_id: Optional[str] = Field(None, max_length=50)
    is_active: bool = True


class SupplierCreate(SupplierBase):
    """Supplier creation schema."""
    pass


class SupplierUpdate(BaseSchema):
    """Supplier update schema."""
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    tax_id: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class SupplierResponse(SupplierBase):
    """Supplier response schema."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

// src/app/schemas/supplier.py
"""
Supplier schemas.
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr

from app.schemas.common import BaseSchema, TimestampMixin


class SupplierBase(BaseModel):
    """Base supplier schema."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=50)
    address: Optional[str] = None
    tax_id: Optional[str] = Field(default=None, max_length=50)
    is_active: bool = True


class SupplierCreate(SupplierBase):
    """Supplier creation schema."""
    pass


class SupplierUpdate(BaseModel):
    """Supplier update schema."""
    code: Optional[str] = Field(default=None, min_length=1, max_length=50)
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=50)
    address: Optional[str] = None
    tax_id: Optional[str] = Field(default=None, max_length=50)
    is_active: Optional[bool] = None


class SupplierResponse(SupplierBase, TimestampMixin):
    """Supplier response schema."""
    id: str
    purchase_orders_count: Optional[int] = 0
    invoices_count: Optional[int] = 0
    delivery_notes_count: Optional[int] = 0

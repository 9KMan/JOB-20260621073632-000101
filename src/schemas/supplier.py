// src/schemas/supplier.py
"""Supplier schemas."""
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.schemas.common import BaseSchema, PaginatedResponse, TimestampMixin, SoftDeleteMixin


class SupplierBase(BaseSchema):
    """Base supplier schema."""
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    tax_id: Optional[str] = Field(None, max_length=50)
    is_active: bool = True


class SupplierCreate(SupplierBase):
    """Schema for creating a supplier."""
    pass


class SupplierUpdate(BaseSchema):
    """Schema for updating a supplier."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    tax_id: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class SupplierResponse(SupplierBase, TimestampMixin, SoftDeleteMixin):
    """Schema for supplier response."""
    id: UUID
    purchase_orders_count: Optional[int] = 0
    invoices_count: Optional[int] = 0
    delivery_notes_count: Optional[int] = 0


class SupplierListResponse(PaginatedResponse[SupplierResponse]):
    """Schema for paginated supplier list."""
    pass


class SupplierSummary(BaseSchema):
    """Lightweight supplier summary."""
    id: UUID
    name: str
    code: str

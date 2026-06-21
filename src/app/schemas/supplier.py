// src/app/schemas/supplier.py
"""
Supplier schemas for API request/response validation.
"""
from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr

from app.schemas.base import BaseSchema, TimestampSchema, PaginationParams, PaginatedResponse


# Request schemas
class SupplierCreate(BaseSchema):
    """Schema for creating a supplier."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    tax_id: Optional[str] = Field(None, max_length=50)
    bank_account: Optional[str] = Field(None, max_length=100)
    payment_terms_days: int = Field(default=30, ge=0)


class SupplierUpdate(BaseSchema):
    """Schema for updating a supplier."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    tax_id: Optional[str] = Field(None, max_length=50)
    bank_account: Optional[str] = Field(None, max_length=100)
    payment_terms_days: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


# Response schemas
class SupplierResponse(TimestampSchema):
    """Supplier response schema."""
    id: UUID
    code: str
    name: str
    email: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    tax_id: Optional[str]
    bank_account: Optional[str]
    payment_terms_days: int
    is_active: bool


class SupplierBrief(BaseSchema):
    """Brief supplier information."""
    id: UUID
    code: str
    name: str


class SupplierListResponse(PaginatedResponse[SupplierResponse]):
    """Paginated supplier list response."""
    pass

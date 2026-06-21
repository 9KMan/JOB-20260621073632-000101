# src/app/schemas/supplier.py
"""Supplier schemas."""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, EmailStr, ConfigDict

from src.app.schemas.base import BaseSchema


class SupplierBase(BaseSchema):
    """Base supplier schema."""
    
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    tax_id: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=50)
    is_active: bool = True


class SupplierCreate(SupplierBase):
    """Schema for creating a supplier."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "SUP001",
                "name": "Acme Corporation",
                "tax_id": "123-45-6789",
                "address": "123 Main Street",
                "city": "New York",
                "country": "USA",
                "contact_email": "contact@acme.com",
                "contact_phone": "+1-555-0100",
            }
        }
    )


class SupplierUpdate(BaseSchema):
    """Schema for updating a supplier."""
    
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    tax_id: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class SupplierResponse(SupplierBase):
    """Schema for supplier response."""
    
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "code": "SUP001",
                "name": "Acme Corporation",
                "tax_id": "123-45-6789",
                "address": "123 Main Street",
                "city": "New York",
                "country": "USA",
                "contact_email": "contact@acme.com",
                "contact_phone": "+1-555-0100",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "deleted_at": None,
            }
        }
    )


class SupplierListResponse(BaseSchema):
    """Schema for paginated supplier list response."""
    
    items: list[SupplierResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool

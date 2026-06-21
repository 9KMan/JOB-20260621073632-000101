// src/schemas/vendor.py
"""Vendor schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, EmailStr


class VendorBase(BaseModel):
    """Base vendor schema."""
    
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    tax_id: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    payment_terms_days: int = Field(default=30, ge=0)
    bank_name: Optional[str] = Field(None, max_length=255)
    bank_account: Optional[str] = Field(None, max_length=100)


class VendorCreate(VendorBase):
    """Vendor creation schema."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "VND-001",
                "name": "Acme Corporation",
                "tax_id": "12-3456789",
                "email": "contact@acme.com",
                "phone": "+1-555-0100",
                "address": "123 Main St",
                "city": "New York",
                "country": "USA",
                "postal_code": "10001",
                "payment_terms_days": 30
            }
        }
    )


class VendorUpdate(BaseModel):
    """Vendor update schema."""
    
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    tax_id: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None
    payment_terms_days: Optional[int] = Field(None, ge=0)
    bank_name: Optional[str] = Field(None, max_length=255)
    bank_account: Optional[str] = Field(None, max_length=100)


class VendorResponse(BaseModel):
    """Vendor response schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    code: str
    name: str
    tax_id: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    is_active: bool
    payment_terms_days: int
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# app/schemas/vendor.py
"""Vendor schemas."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class VendorBase(BaseModel):
    """Base vendor schema."""

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    tax_id: Optional[str] = Field(None, max_length=50)
    bank_name: Optional[str] = Field(None, max_length=255)
    bank_account: Optional[str] = Field(None, max_length=100)
    payment_terms_days: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class VendorCreate(VendorBase):
    """Vendor creation request."""

    is_active: bool = True


class VendorUpdate(BaseModel):
    """Vendor update request."""

    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    tax_id: Optional[str] = Field(None, max_length=50)
    bank_name: Optional[str] = Field(None, max_length=255)
    bank_account: Optional[str] = Field(None, max_length=100)
    payment_terms_days: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class VendorResponse(VendorBase):
    """Vendor response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class VendorListResponse(BaseModel):
    """Vendor list response with pagination."""

    items: List[VendorResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

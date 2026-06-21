// src/schemas/supplier.py
"""Supplier-related Pydantic schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.base import BaseSchema, TimestampMixin


class SupplierBase(BaseSchema):
    """Base supplier schema."""

    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=255)
    email: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=50)
    address: Optional[str] = None
    tax_id: Optional[str] = Field(default=None, max_length=50)
    payment_terms: Optional[str] = Field(default=None, max_length=100)
    bank_details: Optional[str] = None
    is_active: bool = True


class SupplierCreate(SupplierBase):
    """Schema for creating a new supplier."""

    pass


class SupplierUpdate(BaseSchema):
    """Schema for updating a supplier."""

    code: Optional[str] = Field(default=None, min_length=1, max_length=50)
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    email: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=50)
    address: Optional[str] = None
    tax_id: Optional[str] = Field(default=None, max_length=50)
    payment_terms: Optional[str] = Field(default=None, max_length=100)
    bank_details: Optional[str] = None
    is_active: Optional[bool] = None


class SupplierResponse(SupplierBase, TimestampMixin):
    """Schema for supplier response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID


class SupplierSummary(BaseSchema):
    """Schema for supplier summary in nested responses."""

    id: UUID
    code: str
    name: str

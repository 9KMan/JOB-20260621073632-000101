// src/schemas/invoice.py
"""Invoice schemas."""
import uuid
import decimal
from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict, field_validator

from src.models.enums import DocumentStatus


class InvoiceLineBase(BaseModel):
    """Base schema for Invoice line."""
    line_number: int = Field(..., ge=1)
    product_code: Optional[str] = Field(None, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    quantity: decimal.Decimal = Field(..., gt=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: decimal.Decimal = Field(..., ge=0)
    line_amount: decimal.Decimal = Field(..., ge=0)
    tax_rate: decimal.Decimal = Field(default=decimal.Decimal("0.0000"), ge=0)
    tax_amount: decimal.Decimal = Field(default=decimal.Decimal("0.00"), ge=0)
    notes: Optional[str] = Field(None, max_length=500)


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating an Invoice line."""
    pass


class InvoiceLineUpdate(BaseModel):
    """Schema for updating an Invoice line."""
    product_code: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    quantity: Optional[decimal.Decimal] = Field(None, gt=0)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    unit_price: Optional[decimal.Decimal] = Field(None, ge=0)
    line_amount: Optional[decimal.Decimal] = Field(None, ge=0)
    tax_rate: Optional[decimal.Decimal] = Field(None, ge=0)
    tax_amount: Optional[decimal.Decimal] = Field(None, ge=0)
    notes: Optional[str] = Field(None, max_length=500)


class InvoiceLineResponse(InvoiceLineBase):
    """Schema for Invoice line response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    invoice_id: uuid.UUID
    is_matched: bool
    matched_quantity: decimal.Decimal
    created_at: datetime
    updated_at: datetime


class InvoiceBase(BaseModel):
    """Base schema for Invoice."""
    invoice_number: str = Field(..., min_length=1, max_length=100)
    supplier_id: str = Field(..., min_length=1, max_length=100)
    supplier_name: str = Field(..., min_length=1, max_length=255)
    supplier_reference: Optional[str] = Field(None, max_length=100)
    purchase_order_id: Optional[uuid.UUID] = None
    invoice_date: date
    due_date: Optional[date] = None
    currency: str = Field(default="USD", max_length=3)
    payment_terms: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=1000)
    metadata: Optional[str] = Field(None, max_length=2000)


class InvoiceCreate(InvoiceBase):
    """Schema for creating an Invoice."""
    subtotal: decimal.Decimal = Field(default=decimal.Decimal("0.00"), ge=0)
    tax_amount: decimal.Decimal = Field(default=decimal.Decimal("0.00"), ge=0)
    total_amount: decimal.Decimal = Field(..., ge=0)
    amount_paid: decimal.Decimal = Field(default=decimal.Decimal("0.00"), ge=0)
    status: DocumentStatus = DocumentStatus.SUBMITTED
    lines: List[InvoiceLineCreate] = Field(default_factory=list)


class InvoiceUpdate(BaseModel):
    """Schema for updating an Invoice."""
    supplier_id: Optional[str] = Field(None, max_length=100)
    supplier_name: Optional[str] = Field(None, max_length=255)
    supplier_reference: Optional[str] = Field(None, max_length=100)
    purchase_order_id: Optional[uuid.UUID] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    subtotal: Optional[decimal.Decimal] = Field(None, ge=0)
    tax_amount: Optional[decimal.Decimal] = Field(None, ge=0)
    total_amount: Optional[decimal.Decimal] = Field(None, ge=0)
    amount_paid: Optional[decimal.Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    status: Optional[DocumentStatus] = None
    payment_terms: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=1000)
    metadata: Optional[str] = Field(None, max_length=2000)


class InvoiceResponse(InvoiceBase):
    """Schema for Invoice response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    subtotal: decimal.Decimal
    tax_amount: decimal.Decimal
    total_amount: decimal.Decimal
    amount_paid: decimal.Decimal
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    lines: List[InvoiceLineResponse] = Field(default_factory=list)

    @field_validator("lines", mode="before")
    @classmethod
    def validate_lines(cls, v):
        return v if v else []

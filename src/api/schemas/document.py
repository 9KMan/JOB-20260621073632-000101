// src/api/schemas/document.py
"""Document schemas for request/response validation."""
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from src.models.document import DocumentType, DocumentStatus


class DocumentTypeEnum(str, DocumentType):
    """Document type enum."""
    INVOICE = "INVOICE"
    DELIVERY_NOTE = "DELIVERY_NOTE"
    PURCHASE_ORDER = "PURCHASE_ORDER"


class DocumentLineCreate(BaseModel):
    """Schema for creating a document line."""
    line_number: int = Field(..., ge=1)
    item_code: Optional[str] = Field(None, max_length=50)
    description: str = Field(..., max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    total_amount: Decimal = Field(..., ge=0)
    uom: Optional[str] = Field(None, max_length=20)
    tax_code: Optional[str] = Field(None, max_length=20)

    @field_validator("total_amount", mode="before")
    @classmethod
    def calculate_total(cls, v, info):
        if v is None:
            values = info.data
            qty = values.get("quantity", Decimal("0"))
            price = values.get("unit_price", Decimal("0"))
            return qty * price
        return v


class DocumentLineResponse(BaseModel):
    """Schema for document line response."""
    id: UUID
    document_id: UUID
    line_number: int
    item_code: Optional[str]
    description: str
    quantity: Decimal
    unit_price: Decimal
    total_amount: Decimal
    uom: Optional[str]
    tax_code: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentCreate(BaseModel):
    """Schema for creating a document."""
    document_type: DocumentTypeEnum
    document_number: str = Field(..., max_length=100)
    supplier_id: UUID
    supplier_name: str = Field(..., max_length=255)
    supplier_reference: Optional[str] = Field(None, max_length=100)
    currency: str = Field(default="USD", max_length=3)
    subtotal: Decimal = Field(..., ge=0)
    tax_amount: Decimal = Field(default=Decimal("0"), ge=0)
    total_amount: Decimal = Field(..., ge=0)
    document_date: datetime
    due_date: Optional[datetime] = None
    status: str = Field(default="DRAFT", max_length=50)
    lines: list[DocumentLineCreate] = Field(default_factory=list)
    metadata: Optional[dict[str, Any]] = None


class DocumentUpdate(BaseModel):
    """Schema for updating a document."""
    document_number: Optional[str] = Field(None, max_length=100)
    supplier_name: Optional[str] = Field(None, max_length=255)
    supplier_reference: Optional[str] = Field(None, max_length=100)
    currency: Optional[str] = Field(None, max_length=3)
    subtotal: Optional[Decimal] = Field(None, ge=0)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    total_amount: Optional[Decimal] = Field(None, ge=0)
    document_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    status: Optional[str] = Field(None, max_length=50)
    metadata: Optional[dict[str, Any]] = None


class DocumentResponse(BaseModel):
    """Schema for document response."""
    id: UUID
    document_type: str
    document_number: str
    supplier_id: UUID
    supplier_name: str
    supplier_reference: Optional[str]
    currency: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    document_date: datetime
    due_date: Optional[datetime]
    status: str
    metadata: Optional[dict[str, Any]]
    lines: list[DocumentLineResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

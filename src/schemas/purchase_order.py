// src/schemas/purchase_order.py
"""Purchase Order schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.document import DocumentLineCreate, DocumentLineResponse, DocumentResponse


class PurchaseOrderBase(BaseModel):
    """Base purchase order schema."""
    document_number: str = Field(..., max_length=100)
    supplier_code: str = Field(..., max_length=100)
    supplier_name: str = Field(..., max_length=255)
    supplier_tax_id: Optional[str] = Field(None, max_length=50)
    document_date: date
    expected_delivery_date: Optional[date] = None
    payment_terms: Optional[str] = Field(None, max_length=100)
    delivery_address: Optional[str] = None
    buyer_name: Optional[str] = Field(None, max_length=255)
    department: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    currency: str = Field(default="USD", max_length=3)


class PurchaseOrderCreate(PurchaseOrderBase):
    """Purchase order creation schema."""
    lines: list[DocumentLineCreate] = Field(..., min_length=1)


class PurchaseOrderUpdate(BaseModel):
    """Purchase order update schema."""
    supplier_code: Optional[str] = Field(None, max_length=100)
    supplier_name: Optional[str] = Field(None, max_length=255)
    supplier_tax_id: Optional[str] = Field(None, max_length=50)
    expected_delivery_date: Optional[date] = None
    payment_terms: Optional[str] = Field(None, max_length=100)
    delivery_address: Optional[str] = None
    buyer_name: Optional[str] = Field(None, max_length=255)
    department: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    status: Optional[str] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    """Purchase order response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    open_amount: Decimal
    lines: list[DocumentLineResponse] = []
    created_at: datetime
    updated_at: datetime

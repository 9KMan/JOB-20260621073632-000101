# src/app/schemas/purchase_order.py
"""Purchase Order schemas."""
import uuid
import decimal
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict

from src.app.schemas.base import BaseSchema
from src.app.schemas.supplier import SupplierResponse


class PurchaseOrderLineBase(BaseSchema):
    """Base PO line schema."""
    
    line_number: int = Field(..., ge=1)
    item_code: Optional[str] = Field(None, max_length=50)
    item_description: str = Field(..., min_length=1, max_length=500)
    quantity: decimal.Decimal = Field(..., gt=0)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    unit_price: decimal.Decimal = Field(..., ge=0)
    tax_rate: decimal.Decimal = Field(default=decimal.Decimal("0.0000"), ge=0)
    received_quantity: decimal.Decimal = Field(default=decimal.Decimal("0.000"), ge=0)
    invoiced_quantity: decimal.Decimal = Field(default=decimal.Decimal("0.000"), ge=0)


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """Schema for creating a PO line."""
    
    pass


class PurchaseOrderLineUpdate(BaseSchema):
    """Schema for updating a PO line."""
    
    item_code: Optional[str] = Field(None, max_length=50)
    item_description: Optional[str] = Field(None, min_length=1, max_length=500)
    quantity: Optional[decimal.Decimal] = Field(None, gt=0)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    unit_price: Optional[decimal.Decimal] = Field(None, ge=0)
    tax_rate: Optional[decimal.Decimal] = Field(None, ge=0)
    received_quantity: Optional[decimal.Decimal] = Field(None, ge=0)
    invoiced_quantity: Optional[decimal.Decimal] = Field(None, ge=0)


class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    """Schema for PO line response."""
    
    id: uuid.UUID
    purchase_order_id: uuid.UUID
    line_total: decimal.Decimal
    tax_amount: decimal.Decimal
    remaining_quantity: decimal.Decimal
    remaining_invoiced_quantity: decimal.Decimal
    created_at: datetime
    updated_at: datetime


class PurchaseOrderBase(BaseSchema):
    """Base PO schema."""
    
    po_number: str = Field(..., min_length=1, max_length=50)
    supplier_id: uuid.UUID
    status: str = Field(default="DRAFT")
    order_date: datetime
    expected_delivery_date: Optional[datetime] = None
    currency: str = Field(default="USD", max_length=3)
    payment_terms: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a PO."""
    
    lines: List[PurchaseOrderLineCreate] = Field(default_factory=list)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "po_number": "PO-2024-001",
                "supplier_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "DRAFT",
                "order_date": "2024-01-15T00:00:00Z",
                "expected_delivery_date": "2024-01-30T00:00:00Z",
                "currency": "USD",
                "payment_terms": "Net 30",
                "notes": "Urgent order",
                "lines": [
                    {
                        "line_number": 1,
                        "item_code": "ITEM001",
                        "item_description": "Widget A",
                        "quantity": 100,
                        "unit_of_measure": "EA",
                        "unit_price": 25.00,
                        "tax_rate": 0.10,
                    }
                ],
            }
        }
    )


class PurchaseOrderUpdate(BaseSchema):
    """Schema for updating a PO."""
    
    po_number: Optional[str] = Field(None, min_length=1, max_length=50)
    supplier_id: Optional[uuid.UUID] = None
    status: Optional[str] = None
    order_date: Optional[datetime] = None
    expected_delivery_date: Optional[datetime] = None
    currency: Optional[str] = Field(None, max_length=3)
    payment_terms: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    is_archived: Optional[bool] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    """Schema for PO response."""
    
    id: uuid.UUID
    subtotal: decimal.Decimal
    tax_amount: decimal.Decimal
    total_amount: decimal.Decimal
    is_archived: bool
    created_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    supplier: Optional[SupplierResponse] = None
    lines: List[PurchaseOrderLineResponse] = Field(default_factory=list)


class PurchaseOrderListResponse(BaseSchema):
    """Schema for paginated PO list response."""
    
    items: list[PurchaseOrderResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool

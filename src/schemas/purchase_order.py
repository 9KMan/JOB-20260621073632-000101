// src/schemas/purchase_order.py
"""Purchase Order schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PurchaseOrderLineBase(BaseModel):
    """Base PO line schema."""
    
    line_number: int = Field(..., ge=1)
    item_code: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_of_measure: str = Field(default="EA", max_length=20)
    unit_price: Decimal = Field(..., ge=0)
    tax_rate: Decimal = Field(default=Decimal("0.0000"), ge=0)
    line_total: Decimal = Field(..., ge=0)
    expected_delivery_date: Optional[date] = None


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """PO line creation schema."""
    pass


class PurchaseOrderLineUpdate(BaseModel):
    """PO line update schema."""
    
    item_code: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit_of_measure: Optional[str] = Field(None, max_length=20)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    tax_rate: Optional[Decimal] = Field(None, ge=0)
    line_total: Optional[Decimal] = Field(None, ge=0)
    expected_delivery_date: Optional[date] = None


class PurchaseOrderLineResponse(BaseModel):
    """PO line response schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    line_number: int
    item_code: str
    description: str
    quantity: Decimal
    unit_of_measure: str
    unit_price: Decimal
    tax_rate: Decimal
    line_total: Decimal
    expected_delivery_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime


class PurchaseOrderBase(BaseModel):
    """Base PO schema."""
    
    po_number: str = Field(..., min_length=1, max_length=50)
    vendor_id: UUID
    order_date: date
    expected_delivery_date: Optional[date] = None
    status: str = Field(default="draft", max_length=50)
    currency: str = Field(default="USD", max_length=3)
    subtotal: Decimal = Field(default=Decimal("0.00"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    total_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    notes: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """PO creation schema."""
    
    lines: List[PurchaseOrderLineCreate] = Field(default_factory=list)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "po_number": "PO-2024-001",
                "vendor_id": "uuid-here",
                "order_date": "2024-01-15",
                "expected_delivery_date": "2024-01-30",
                "status": "draft",
                "currency": "USD",
                "subtotal": Decimal("1000.00"),
                "tax_amount": Decimal("100.00"),
                "total_amount": Decimal("1100.00"),
                "notes": "Urgent order",
                "lines": [
                    {
                        "line_number": 1,
                        "item_code": "ITEM-001",
                        "description": "Widget A",
                        "quantity": Decimal("10"),
                        "unit_of_measure": "EA",
                        "unit_price": Decimal("100.00"),
                        "tax_rate": Decimal("0.1000"),
                        "line_total": Decimal("1100.00")
                    }
                ]
            }
        }
    )


class PurchaseOrderUpdate(BaseModel):
    """PO update schema."""
    
    po_number: Optional[str] = Field(None, min_length=1, max_length=50)
    vendor_id: Optional[UUID] = None
    order_date: Optional[date] = None
    expected_delivery_date: Optional[date] = None
    status: Optional[str] = Field(None, max_length=50)
    currency: Optional[str] = Field(None, max_length=3)
    subtotal: Optional[Decimal] = Field(None, ge=0)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    total_amount: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None


class PurchaseOrderResponse(BaseModel):
    """PO response schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    po_number: str
    vendor_id: UUID
    order_date: date
    expected_delivery_date: Optional[date] = None
    status: str
    currency: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    notes: Optional[str] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    lines: List[PurchaseOrderLineResponse] = Field(default_factory=list)

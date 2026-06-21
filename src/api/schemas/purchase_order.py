// src/api/schemas/purchase_order.py
"""Purchase Order schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class PurchaseOrderLineBase(BaseModel):
    """Base PO line schema."""
    line_number: int = Field(ge=1)
    item_code: Optional[str] = Field(default=None, max_length=50)
    description: str = Field(min_length=1, max_length=500)
    quantity: Decimal = Field(gt=0, decimal_places=3)
    unit_of_measure: Optional[str] = Field(default=None, max_length=20)
    unit_price: Decimal = Field(ge=0, decimal_places=2)
    tax_rate: Optional[Decimal] = Field(default=None, ge=0, le=100)
    expected_delivery_date: Optional[date] = None
    
    @field_validator("line_amount", mode="before")
    @classmethod
    def calculate_line_amount(cls, v, info):
        """Calculate line amount from quantity and unit price."""
        if v is not None:
            return v
        return None


class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    """PO line creation schema."""
    line_amount: Optional[Decimal] = Field(default=None, ge=0)
    
    def calculate_amounts(self) -> tuple[Decimal, Decimal]:
        """Calculate line amount and tax amount."""
        line_amount = self.quantity * self.unit_price
        tax_amount = Decimal("0")
        if self.tax_rate:
            tax_amount = line_amount * (self.tax_rate / 100)
        return line_amount, tax_amount


class PurchaseOrderLineUpdate(BaseModel):
    """PO line update schema."""
    item_code: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit_of_measure: Optional[str] = None
    unit_price: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    expected_delivery_date: Optional[date] = None


class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    """PO line response schema."""
    id: UUID
    purchase_order_id: UUID
    line_amount: Decimal
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class PurchaseOrderBase(BaseModel):
    """Base PO schema."""
    po_number: str = Field(min_length=1, max_length=50)
    supplier_id: UUID
    order_date: date
    expected_delivery_date: Optional[date] = None
    currency: str = Field(default="USD", min_length=3, max_length=3)
    notes: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """PO creation schema."""
    lines: List[PurchaseOrderLineCreate] = Field(min_length=1)
    total_amount: Optional[Decimal] = None
    
    def calculate_total(self) -> Decimal:
        """Calculate total amount from lines."""
        return sum(
            line.quantity * line.unit_price
            for line in self.lines
        )


class PurchaseOrderUpdate(BaseModel):
    """PO update schema."""
    supplier_id: Optional[UUID] = None
    status: Optional[str] = None
    expected_delivery_date: Optional[date] = None
    notes: Optional[str] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    """PO response schema."""
    id: UUID
    status: str
    total_amount: Decimal
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    lines: List[PurchaseOrderLineResponse] = []
    
    model_config = {"from_attributes": True}


class PurchaseOrderListResponse(BaseModel):
    """PO list response schema."""
    items: List[PurchaseOrderResponse]
    total: int
    page: int
    size: int
    pages: int

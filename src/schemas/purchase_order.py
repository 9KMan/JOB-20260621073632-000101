# src/schemas/purchase_order.py
"""Purchase Order Pydantic schemas."""
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from datetime import date

from pydantic import BaseModel, Field, ConfigDict


# Line Items
class PurchaseOrderLineItemBase(BaseModel):
    """Base schema for PO line items."""
    
    line_number: int = Field(..., description="Line number")
    sku: Optional[str] = Field(None, max_length=100, description="SKU code")
    description: str = Field(..., max_length=500, description="Item description")
    quantity_ordered: Decimal = Field(..., gt=0, description="Ordered quantity")
    quantity_received: Decimal = Field(default=Decimal("0.00"), ge=0, description="Received quantity")
    quantity_invoiced: Decimal = Field(default=Decimal("0.00"), ge=0, description="Invoiced quantity")
    unit_of_measure: str = Field(default="EA", max_length=20, description="Unit of measure")
    unit_price: Decimal = Field(..., gt=0, description="Unit price")


class PurchaseOrderLineItemCreate(PurchaseOrderLineItemBase):
    """Schema for creating PO line items."""
    pass


class PurchaseOrderLineItemResponse(PurchaseOrderLineItemBase):
    """Schema for PO line item response."""
    
    id: UUID
    purchase_order_id: UUID
    line_total: Decimal
    created_at: str
    updated_at: str
    
    model_config = {"from_attributes": True}


# Purchase Order
class PurchaseOrderBase(BaseModel):
    """Base schema for purchase orders."""
    
    po_number: str = Field(..., max_length=50, description="PO number")
    supplier_id: str = Field(..., max_length=50, description="Supplier ID")
    supplier_name: str = Field(..., max_length=255, description="Supplier name")
    supplier_code: Optional[str] = Field(None, max_length=50, description="Supplier code")
    order_date: date = Field(..., description="Order date")
    expected_delivery_date: Optional[date] = Field(None, description="Expected delivery date")
    currency: str = Field(default="USD", max_length=3, description="Currency code")
    subtotal: Decimal = Field(..., ge=0, description="Subtotal amount")
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0, description="Tax amount")
    total_amount: Decimal = Field(..., ge=0, description="Total amount")
    notes: Optional[str] = Field(None, description="Notes")
    terms_and_conditions: Optional[str] = Field(None, description="Terms and conditions")


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating purchase orders."""
    
    line_items: List[PurchaseOrderLineItemCreate] = Field(
        default_factory=list,
        description="Line items"
    )


class PurchaseOrderUpdate(BaseModel):
    """Schema for updating purchase orders."""
    
    supplier_name: Optional[str] = Field(None, max_length=255, description="Supplier name")
    supplier_code: Optional[str] = Field(None, max_length=50, description="Supplier code")
    expected_delivery_date: Optional[date] = Field(None, description="Expected delivery date")
    subtotal: Optional[Decimal] = Field(None, ge=0, description="Subtotal amount")
    tax_amount: Optional[Decimal] = Field(None, ge=0, description="Tax amount")
    total_amount: Optional[Decimal] = Field(None, ge=0, description="Total amount")
    status: Optional[str] = Field(None, description="PO status")
    notes: Optional[str] = Field(None, description="Notes")
    terms_and_conditions: Optional[str] = Field(None, description="Terms and conditions")
    line_items: Optional[List[PurchaseOrderLineItemCreate]] = Field(
        None,
        description="Line items"
    )


class PurchaseOrderResponse(PurchaseOrderBase):
    """Schema for purchase order response."""
    
    id: UUID
    status: str
    is_deleted: str
    created_at: str
    updated_at: str
    line_items: List[PurchaseOrderLineItemResponse] = []
    
    model_config = {"from_attributes": True}


class PurchaseOrderListResponse(BaseModel):
    """Schema for purchase order list response."""
    
    id: UUID
    po_number: str
    supplier_name: str
    order_date: date
    total_amount: Decimal
    status: str
    created_at: str
    
    model_config = {"from_attributes": True}

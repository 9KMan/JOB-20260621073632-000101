# src/schemas/invoice.py
"""Invoice Pydantic schemas."""
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from datetime import date

from pydantic import BaseModel, Field


# Line Items
class InvoiceLineItemBase(BaseModel):
    """Base schema for invoice line items."""
    
    line_number: str = Field(..., max_length=10, description="Line number")
    sku: Optional[str] = Field(None, max_length=100, description="SKU code")
    description: str = Field(..., max_length=500, description="Item description")
    quantity: Decimal = Field(..., gt=0, description="Quantity")
    unit_of_measure: str = Field(default="EA", max_length=20, description="Unit of measure")
    unit_price: Decimal = Field(..., gt=0, description="Unit price")


class InvoiceLineItemCreate(InvoiceLineItemBase):
    """Schema for creating invoice line items."""
    pass


class InvoiceLineItemResponse(InvoiceLineItemBase):
    """Schema for invoice line item response."""
    
    id: UUID
    invoice_id: UUID
    line_total: Decimal
    created_at: str
    updated_at: str
    
    model_config = {"from_attributes": True}


# Invoice
class InvoiceBase(BaseModel):
    """Base schema for invoices."""
    
    invoice_number: str = Field(..., max_length=50, description="Invoice number")
    supplier_id: str = Field(..., max_length=50, description="Supplier ID")
    supplier_name: str = Field(..., max_length=255, description="Supplier name")
    supplier_code: Optional[str] = Field(None, max_length=50, description="Supplier code")
    po_reference: Optional[str] = Field(None, max_length=50, description="PO reference")
    invoice_date: date = Field(..., description="Invoice date")
    due_date: Optional[date] = Field(None, description="Due date")
    currency: str = Field(default="USD", max_length=3, description="Currency code")
    subtotal: Decimal = Field(..., ge=0, description="Subtotal amount")
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0, description="Tax amount")
    total_amount: Decimal = Field(..., ge=0, description="Total amount")
    notes: Optional[str] = Field(None, description="Notes")


class InvoiceCreate(InvoiceBase):
    """Schema for creating invoices."""
    
    line_items: List[InvoiceLineItemCreate] = Field(
        default_factory=list,
        description="Line items"
    )


class InvoiceUpdate(BaseModel):
    """Schema for updating invoices."""
    
    supplier_name: Optional[str] = Field(None, max_length=255, description="Supplier name")
    supplier_code: Optional[str] = Field(None, max_length=50, description="Supplier code")
    due_date: Optional[date] = Field(None, description="Due date")
    subtotal: Optional[Decimal] = Field(None, ge=0, description="Subtotal amount")
    tax_amount: Optional[Decimal] = Field(None, ge=0, description="Tax amount")
    total_amount: Optional[Decimal] = Field(None, ge=0, description="Total amount")
    status: Optional[str] = Field(None, description="Invoice status")
    notes: Optional[str] = Field(None, description="Notes")
    payment_reference: Optional[str] = Field(None, max_length=100, description="Payment reference")
    line_items: Optional[List[InvoiceLineItemCreate]] = Field(
        None,
        description="Line items"
    )


class InvoiceResponse(InvoiceBase):
    """Schema for invoice response."""
    
    id: UUID
    status: str
    payment_reference: Optional[str]
    is_deleted: str
    created_at: str
    updated_at: str
    line_items: List[InvoiceLineItemResponse] = []
    
    model_config = {"from_attributes": True}


class InvoiceListResponse(BaseModel):
    """Schema for invoice list response."""
    
    id: UUID
    invoice_number: str
    supplier_name: str
    invoice_date: date
    total_amount: Decimal
    status: str
    created_at: str
    
    model_config = {"from_attributes": True}

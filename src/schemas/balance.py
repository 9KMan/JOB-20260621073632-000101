// src/schemas/balance.py
"""Balance schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BalanceBase(BaseModel):
    """Base balance schema."""
    
    balance_type: str
    purchase_order_id: Optional[UUID] = None
    invoice_id: Optional[UUID] = None
    delivery_note_id: Optional[UUID] = None
    original_po_amount: Decimal = Field(default=Decimal("0.00"))
    original_invoice_amount: Optional[Decimal] = None
    original_delivery_amount: Optional[Decimal] = None
    matched_amount: Decimal = Field(default=Decimal("0.00"))
    matched_quantity: Decimal = Field(default=Decimal("0.000"))
    outstanding_amount: Decimal = Field(default=Decimal("0.00"))
    outstanding_quantity: Decimal = Field(default=Decimal("0.000"))
    item_code: Optional[str] = None


class BalanceCreate(BalanceBase):
    """Balance creation schema."""
    
    match_id: Optional[UUID] = None


class BalanceUpdate(BaseModel):
    """Balance update schema."""
    
    matched_amount: Optional[Decimal] = None
    matched_quantity: Optional[Decimal] = None
    outstanding_amount: Optional[Decimal] = None
    outstanding_quantity: Optional[Decimal] = None
    is_resolved: Optional[bool] = None
    resolution_date: Optional[date] = None
    resolution_notes: Optional[str] = None


class BalanceResponse(BaseModel):
    """Balance response schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    balance_type: str
    purchase_order_id: Optional[UUID] = None
    invoice_id: Optional[UUID] = None
    delivery_note_id: Optional[UUID] = None
    original_po_amount: Decimal
    original_invoice_amount: Optional[Decimal] = None
    original_delivery_amount: Optional[Decimal] = None
    matched_amount: Decimal
    matched_quantity: Decimal
    outstanding_amount: Decimal
    outstanding_quantity: Decimal
    is_resolved: bool
    resolution_date: Optional[date] = None
    resolution_notes: Optional[str] = None
    match_id: Optional[UUID] = None
    item_code: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class BalanceSummary(BaseModel):
    """Balance summary for dashboard."""
    
    total_balances: int
    resolved: int
    outstanding: int
    total_outstanding_amount: Decimal

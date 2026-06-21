# src/schemas/balance_ledger.py
"""Balance Ledger Pydantic schemas."""
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from datetime import date

from pydantic import BaseModel, Field


class BalanceLedgerResponse(BaseModel):
    """Schema for balance ledger response."""
    
    id: UUID
    po_id: UUID
    invoice_id: Optional[UUID]
    balance_type: str
    po_total_amount: Decimal
    invoice_amount: Optional[Decimal]
    matched_amount: Decimal
    balance_amount: Decimal
    po_quantity: Decimal
    invoiced_quantity: Decimal
    delivered_quantity: Decimal
    matched_quantity: Decimal
    as_of_date: date
    is_settled: str
    settled_date: Optional[date]
    notes: Optional[str]
    created_at: str
    updated_at: str
    
    model_config = {"from_attributes": True}


class BalanceSummary(BaseModel):
    """Summary of balances."""
    
    total_open_po_amount: Decimal = Field(..., description="Total open PO amount")
    total_invoiced_amount: Decimal = Field(..., description="Total invoiced amount")
    total_matched_amount: Decimal = Field(..., description="Total matched amount")
    total_outstanding_balance: Decimal = Field(..., description="Total outstanding balance")
    pending_match_count: int = Field(..., description="Number of pending matches")
    settled_count: int = Field(..., description="Number of settled balances")


class BalanceLedgerListResponse(BaseModel):
    """Schema for balance ledger list response."""
    
    id: UUID
    po_id: UUID
    invoice_id: Optional[UUID]
    balance_type: str
    balance_amount: Decimal
    as_of_date: date
    is_settled: str
    created_at: str
    
    model_config = {"from_attributes": True}

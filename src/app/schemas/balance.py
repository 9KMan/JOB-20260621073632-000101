// src/app/schemas/balance.py
"""Balance ledger schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BalanceResponse(BaseModel):
    """Balance response schema."""
    
    id: str
    document_type: str
    document_id: str
    document_line_id: Optional[str] = None
    
    original_amount: Decimal
    matched_amount: Decimal
    balance_amount: Decimal
    
    original_quantity: Decimal
    matched_quantity: Decimal
    balance_quantity: Decimal
    
    balance_percentage: Decimal
    status: str
    currency: str
    
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class BalanceListResponse(BaseModel):
    """Balance list response with pagination."""
    
    balances: list[BalanceResponse]
    total: int
    page: int
    page_size: int


class BalanceSummary(BaseModel):
    """Balance summary for a document."""
    
    document_type: str
    document_id: str
    original_amount: Decimal
    matched_amount: Decimal
    balance_amount: Decimal
    balance_percentage: Decimal
    line_count: int
    closed_lines: int
    partial_lines: int
    open_lines: int
    
    model_config = ConfigDict(from_attributes=True)


class BalanceUpdateRequest(BaseModel):
    """Request to update a balance record."""
    
    notes: Optional[str] = None


class BalanceAdjustmentRequest(BaseModel):
    """Request to manually adjust a balance."""
    
    balance_id: str
    adjustment_amount: Decimal
    adjustment_quantity: Optional[Decimal] = None
    reason: str

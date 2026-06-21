// src/app/schemas/balance.py
"""Balance Pydantic schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class BalanceTransactionBase(BaseModel):
    """Base balance transaction schema."""
    balance_id: UUID
    transaction_type: str = Field(..., max_length=10)
    amount: Decimal = Field(..., gt=0)
    description: str = Field(..., max_length=500)


class BalanceTransactionCreate(BalanceTransactionBase):
    """Balance transaction creation schema."""
    match_id: Optional[UUID] = None


class BalanceTransactionResponse(BalanceTransactionBase):
    """Balance transaction response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    balance_id: UUID
    match_id: Optional[UUID] = None
    balance_before: Decimal
    balance_after: Decimal
    created_at: datetime
    updated_at: datetime


class BalanceBase(BaseModel):
    """Base balance schema."""
    document_type: str = Field(..., max_length=20)
    document_id: UUID
    document_number: str = Field(..., max_length=50)
    supplier_id: UUID
    original_amount: Decimal
    currency: str = Field(default="USD", max_length=3)


class BalanceCreate(BalanceBase):
    """Balance creation schema."""
    document_date: datetime
    notes: Optional[str] = None


class BalanceUpdate(BaseModel):
    """Balance update schema."""
    status: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = None


class BalanceResponse(BalanceBase):
    """Balance response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    original_amount: Decimal
    matched_amount: Decimal
    balance_amount: Decimal
    document_date: datetime
    status: str
    notes: Optional[str] = None
    transactions: List[BalanceTransactionResponse] = []
    created_at: datetime
    updated_at: datetime

// src/app/schemas/balance.py
"""
Balance Ledger schemas.
"""
from typing import Optional, List
from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field

from app.schemas.common import BaseSchema, TimestampMixin


class BalanceLedgerBase(BaseModel):
    """Base balance ledger schema."""
    document_type: str
    document_id: str
    document_number: str
    balance_type: str
    po_id: Optional[str] = None
    po_number: Optional[str] = None


class BalanceLedgerCreate(BalanceLedgerBase):
    """Balance ledger creation schema."""
    original_amount: Decimal
    original_quantity: Decimal


class BalanceLedgerUpdate(BaseModel):
    """Balance ledger update schema."""
    matched_amount: Optional[Decimal] = None
    matched_quantity: Optional[Decimal] = None
    remaining_amount: Optional[Decimal] = None
    remaining_quantity: Optional[Decimal] = None
    is_settled: Optional[str] = None
    settled_at: Optional[date] = None
    notes: Optional[str] = None


class BalanceLedgerResponse(BalanceLedgerBase, TimestampMixin):
    """Balance ledger response schema."""
    id: str
    original_amount: Decimal
    matched_amount: Decimal
    remaining_amount: Decimal
    original_quantity: Decimal
    matched_quantity: Decimal
    remaining_quantity: Decimal
    is_settled: str
    settled_at: Optional[date] = None
    notes: Optional[str] = None
    is_fully_settled: bool = False
    settlement_percentage: Decimal

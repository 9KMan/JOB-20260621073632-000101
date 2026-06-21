// src/api/schemas/balance.py
from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from decimal import Decimal
from src.models.balance import BalanceType


class BalanceEntryResponse(BaseModel):
    """Balance entry response schema."""
    id: UUID
    balance_type: BalanceType
    purchase_order_id: Optional[UUID] = None
    invoice_id: Optional[UUID] = None
    delivery_note_id: Optional[UUID] = None
    original_amount: Decimal
    matched_amount: Decimal
    remaining_amount: Decimal
    po_line_id: Optional[UUID] = None
    invoice_line_id: Optional[UUID] = None
    dn_line_id: Optional[UUID] = None
    match_id: Optional[UUID] = None
    notes: Optional[str] = None
    created_at: str
    
    class Config:
        from_attributes = True


class BalanceSummary(BaseModel):
    """Summary of balances for a document."""
    document_type: str
    document_id: UUID
    document_number: str
    original_amount: Decimal
    total_matched: Decimal
    remaining_balance: Decimal
    balance_percentage: Decimal

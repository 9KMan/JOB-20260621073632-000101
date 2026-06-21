// src/schemas/balance.py
"""Balance ledger schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import ConfigDict

from src.models.balance import BalanceType
from src.schemas.common import BaseSchema, TimestampSchema


class BalanceLedgerResponse(TimestampSchema):
    """Balance ledger response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    invoice_id: Optional[UUID] = None
    purchase_order_id: Optional[UUID] = None
    delivery_note_id: Optional[UUID] = None
    
    balance_type: BalanceType
    
    original_amount: Decimal
    matched_amount: Decimal
    remaining_amount: Decimal
    
    original_quantity: Decimal
    matched_quantity: Decimal
    remaining_quantity: Decimal
    
    is_settled: bool

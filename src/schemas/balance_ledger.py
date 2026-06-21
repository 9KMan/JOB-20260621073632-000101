// src/schemas/balance_ledger.py
"""Balance Ledger schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from src.schemas.base import BaseSchema


class BalanceLedgerResponse(BaseSchema):
    """Balance ledger response schema."""
    id: str
    po_id: Optional[str] = None
    invoice_id: Optional[str] = None
    dn_id: Optional[str] = None
    po_line_id: Optional[str] = None
    invoice_line_id: Optional[str] = None
    dn_line_id: Optional[str] = None
    match_result_id: Optional[str] = None
    document_type: str
    original_amount: Decimal
    original_quantity: Decimal
    matched_amount: Decimal
    matched_quantity: Decimal
    remaining_amount: Decimal
    remaining_quantity: Decimal
    balance_type: str
    is_active: str
    notes: Optional[str] = None
    closed_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

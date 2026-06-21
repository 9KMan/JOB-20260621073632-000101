# app/schemas/balance.py
"""Balance Ledger schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class BalanceResponse(BaseModel):
    """Balance ledger response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    invoice_id: Optional[str] = None
    po_id: Optional[str] = None
    dn_id: Optional[str] = None
    balance_type: str
    original_amount: Decimal
    matched_amount: Decimal
    remaining_amount: Decimal
    status: str
    matching_result_id: Optional[str] = None
    notes: Optional[str] = None
    reconciled_at: Optional[str] = None
    reconciled_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class BalanceListResponse(BaseModel):
    """Balance list response with pagination."""

    items: List[BalanceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class BalanceReconciliationRequest(BaseModel):
    """Balance reconciliation request."""

    notes: Optional[str] = None
    write_off: bool = False

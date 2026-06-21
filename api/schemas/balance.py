# api/schemas/balance.py
"""Balance Ledger schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class BalanceLedgerBase(BaseModel):
    """Balance Ledger base schema."""

    balance_type: str = Field(min_length=1, max_length=30)
    document_type: str = Field(min_length=1, max_length=20)
    document_number: str = Field(min_length=1, max_length=50)
    line_id: Optional[str] = None
    line_number: Optional[int] = None
    original_amount: Decimal = Field(ge=0)
    current_balance: Decimal = Field(ge=0)
    matched_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    variance_amount: Decimal = Field(default=Decimal("0.00"))
    match_id: Optional[str] = None
    is_closed: bool = False
    closed_at: Optional[datetime] = None
    closed_reason: Optional[str] = None
    notes: Optional[str] = None


class BalanceLedgerResponse(BalanceLedgerBase):
    """Balance Ledger response schema."""

    id: str
    document_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BalanceLedgerListResponse(BaseModel):
    """Balance Ledger list response schema."""

    id: str
    balance_type: str
    document_type: str
    document_number: str
    original_amount: Decimal
    current_balance: Decimal
    matched_amount: Decimal
    is_closed: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class BalanceSummary(BaseModel):
    """Balance summary response."""

    total_open_pos: int
    total_open_po_amount: Decimal
    total_open_invoices: int
    total_open_invoice_amount: Decimal
    total_pending_dns: int
    total_pending_dn_amount: Decimal
    total_variance: Decimal

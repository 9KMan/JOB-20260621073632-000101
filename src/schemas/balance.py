// src/schemas/balance.py
"""Balance ledger schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.base import PaginatedResponse


class BalanceEntryResponse(BaseModel):
    """Schema for Balance Entry response."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    ledger_id: UUID
    match_id: Optional[UUID] = None
    entry_type: str
    amount: Decimal
    balance_before: Decimal
    balance_after: Decimal
    notes: Optional[str] = None
    created_at: datetime


class BalanceLedgerResponse(BaseModel):
    """Schema for Balance Ledger response."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    document_type: str
    document_id: UUID
    supplier_id: UUID
    original_amount: Decimal
    matched_amount: Decimal
    open_amount: Decimal
    currency: str
    status: str
    reference_document_type: Optional[str] = None
    reference_document_id: Optional[UUID] = None
    notes: Optional[str] = None
    entries: list[BalanceEntryResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class BalanceLedgerListResponse(PaginatedResponse[BalanceLedgerResponse]):
    """Paginated list of Balance Ledgers."""

    pass


class BalanceSummaryResponse(BaseModel):
    """Summary of balances by status."""

    total_open: Decimal
    total_partial: Decimal
    total_resolved: Decimal
    total_open_count: int
    total_partial_count: int
    total_resolved_count: int

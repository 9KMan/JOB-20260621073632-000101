// src/app/schemas/balance.py
"""
Balance Ledger schemas for API request/response validation.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.base import BaseSchema, TimestampSchema, PaginationParams, PaginatedResponse


class BalanceLedgerCreate(BaseSchema):
    """Schema for creating a balance ledger entry."""
    transaction_type: str
    transaction_id: UUID
    source_type: str
    source_id: UUID
    balance_type: str
    original_quantity: Decimal
    original_amount: Decimal
    description: Optional[str] = None


class BalanceLedgerUpdate(BaseSchema):
    """Schema for updating a balance ledger entry."""
    applied_quantity: Optional[Decimal] = None
    applied_amount: Optional[Decimal] = None
    is_settled: Optional[bool] = None


class BalanceLedgerResponse(TimestampSchema):
    """Balance ledger response schema."""
    id: UUID
    transaction_type: str
    transaction_id: UUID
    source_type: str
    source_id: UUID
    balance_type: str
    original_quantity: Decimal
    original_amount: Decimal
    applied_quantity: Decimal
    applied_amount: Decimal
    remaining_quantity: Decimal
    remaining_amount: Decimal
    is_settled: bool
    settled_at: Optional[UUID]
    description: Optional[str]


class BalanceLedgerListResponse(PaginatedResponse[BalanceLedgerResponse]):
    """Paginated balance ledger list response."""
    pass


class BalanceSummary(BaseSchema):
    """Summary of outstanding balances."""
    total_outstanding_quantity: Decimal
    total_outstanding_amount: Decimal
    settled_count: int
    unsettled_count: int
    by_source_type: dict
    by_transaction_type: dict


class BalanceApplication(BaseSchema):
    """Schema for applying balance to transactions."""
    balance_id: UUID
    apply_quantity: Optional[Decimal] = None
    apply_amount: Optional[Decimal] = None
    description: Optional[str] = None

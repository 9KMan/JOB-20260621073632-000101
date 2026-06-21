// src/schemas/balance.py
"""Balance schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from src.models.balance import BalanceDirection, BalanceType
from src.schemas.common import BaseSchema, UUIDMixin


class BalanceCreate(BaseModel):
    """Schema for creating a balance record."""
    balance_type: BalanceType
    direction: BalanceDirection
    original_amount: Decimal
    document_date: date
    due_date: Optional[date] = None
    purchase_order_id: Optional[UUID] = None
    invoice_id: Optional[UUID] = None
    delivery_note_id: Optional[UUID] = None
    currency: str = "USD"


class BalanceUpdate(BaseModel):
    """Schema for updating a balance record."""
    matched_amount: Optional[Decimal] = None
    remaining_amount: Optional[Decimal] = None
    is_settled: Optional[bool] = None
    settled_at: Optional[date] = None


class BalanceResponse(UUIDMixin, BaseSchema):
    """Response schema for balance records."""
    balance_type: BalanceType
    direction: BalanceDirection
    original_amount: Decimal
    matched_amount: Decimal
    remaining_amount: Decimal
    document_date: date
    due_date: Optional[date]
    is_settled: bool
    settled_at: Optional[date]
    purchase_order_id: Optional[UUID]
    invoice_id: Optional[UUID]
    delivery_note_id: Optional[UUID]
    currency: str
    created_at: datetime
    updated_at: datetime


class BalanceSummaryResponse(BaseSchema):
    """Summary response for balance listings."""
    id: UUID
    balance_type: BalanceType
    original_amount: Decimal
    remaining_amount: Decimal
    is_settled: bool
    currency: str
    created_at: datetime


class BalanceLedgerResponse(BaseModel):
    """Response for balance ledger overview."""
    total_open_po_balance: Decimal
    total_open_invoice_balance: Decimal
    total_open_delivery_balance: Decimal
    unsettled_count: int
    total_records: int

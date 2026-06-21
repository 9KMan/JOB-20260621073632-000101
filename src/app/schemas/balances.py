# src/app/schemas/balances.py
"""Balance ledger schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.app.schemas.common import BaseSchema, TimestampMixin, UUIDMixin


class BalanceLedgerBase(BaseSchema):
    """Base balance ledger schema."""
    document_type: str = Field(..., min_length=1, max_length=20)
    document_id: UUID
    line_id: Optional[UUID] = None
    balance_type: str = Field(..., min_length=1, max_length=20)
    quantity: Decimal = Field(default=Decimal("0.000"))
    amount: Decimal = Field(default=Decimal("0.00"))
    reference_type: Optional[str] = Field(None, max_length=50)
    reference_id: Optional[UUID] = None
    is_settled: bool = False
    settled_at: Optional[date] = None
    notes: Optional[str] = None


class BalanceLedgerCreate(BalanceLedgerBase):
    """Schema for creating a balance ledger entry."""
    pass


class BalanceLedgerUpdate(BaseSchema):
    """Schema for updating a balance ledger entry."""
    balance_type: Optional[str] = Field(None, min_length=1, max_length=20)
    quantity: Optional[Decimal] = None
    amount: Optional[Decimal] = None
    is_settled: Optional[bool] = None
    settled_at: Optional[date] = None
    notes: Optional[str] = None


class BalanceLedgerRead(UUIDMixin, TimestampMixin, BalanceLedgerBase):
    """Schema for reading a balance ledger entry."""
    pass


class BalanceSummary(BaseModel):
    """Summary of balances for a document."""
    document_type: str
    document_id: UUID
    total_open_quantity: Decimal
    total_open_amount: Decimal
    total_utilized_quantity: Decimal
    total_utilized_amount: Decimal
    total_remaining_quantity: Decimal
    total_remaining_amount: Decimal
    line_balances: list[BalanceLedgerRead] = Field(default_factory=list)

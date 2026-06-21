// src/schemas/balance.py
"""Balance ledger schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.schemas.common import BaseSchema, TimestampMixin


class BalanceLedgerBase(BaseSchema):
    """Base balance ledger schema."""
    balance_type: str
    direction: str
    status: str


class BalanceLedgerCreate(BaseSchema):
    """Schema for creating a balance entry."""
    balance_type: str
    direction: str
    source_document_type: str
    source_document_id: UUID
    source_line_id: Optional[UUID] = None
    related_document_type: Optional[str] = None
    related_document_id: Optional[UUID] = None
    original_amount: Decimal
    balance_amount: Decimal
    currency: str = "USD"
    matching_record_id: Optional[UUID] = None
    notes: Optional[str] = None


class BalanceLedgerUpdate(BaseSchema):
    """Schema for updating a balance entry."""
    balance_amount: Optional[Decimal] = None
    status: Optional[str] = None
    resolution_type: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolved_by_id: Optional[UUID] = None
    resolved_at: Optional[datetime] = None


class BalanceLedgerResponse(BalanceLedgerBase, TimestampMixin):
    """Schema for balance ledger response."""
    id: UUID
    source_document_type: str
    source_document_id: UUID
    source_line_id: Optional[UUID] = None
    related_document_type: Optional[str] = None
    related_document_id: Optional[UUID] = None
    original_amount: Decimal
    balance_amount: Decimal
    resolved_amount: Decimal
    currency: str
    matching_record_id: Optional[UUID] = None
    resolution_type: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolved_by_id: Optional[UUID] = None
    resolved_at: Optional[datetime] = None
    transaction_reference: Optional[str] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class BalanceResolutionRequest(BaseSchema):
    """Request to resolve a balance."""
    resolution_type: str
    resolve_amount: Optional[Decimal] = None
    resolution_notes: Optional[str] = None
    transaction_reference: Optional[str] = None


class BalanceSummary(BaseSchema):
    """Summary of balances."""
    total_open: int
    total_resolved: int
    total_disputed: int
    total_open_amount: Decimal
    total_resolved_amount: Decimal


class BalanceByDocument(BaseSchema):
    """Balance grouped by document."""
    document_type: str
    document_id: UUID
    document_number: str
    balance_count: int
    total_balance_amount: Decimal

// src/schemas/match.py
"""Match schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import Field, ConfigDict

from src.schemas.common import BaseSchema
from src.schemas.invoice import InvoiceResponse
from src.schemas.purchase_order import PurchaseOrderResponse
from src.schemas.delivery_note import DeliveryNoteResponse
from src.models.enums import MatchStatus, MatchDecision, MatchType


class MatchLineBase(BaseSchema):
    """Base match line schema."""
    line_number: int = Field(..., ge=1)
    po_line_id: Optional[UUID] = None
    invoice_line_id: Optional[UUID] = None
    delivery_line_id: Optional[UUID] = None
    match_type: MatchType
    score: Decimal = Field(default=Decimal("0.0000"))
    quantity_matched: Decimal = Field(default=Decimal("0.0000"))
    quantity_variance: Decimal = Field(default=Decimal("0.0000"))
    amount_matched: Decimal = Field(default=Decimal("0.00"))
    amount_variance: Decimal = Field(default=Decimal("0.00"))
    is_partial: bool = False
    notes: Optional[str] = None


class MatchLineCreate(MatchLineBase):
    """Match line creation schema."""
    pass


class MatchLineUpdate(BaseSchema):
    """Match line update schema."""
    po_line_id: Optional[UUID] = None
    invoice_line_id: Optional[UUID] = None
    delivery_line_id: Optional[UUID] = None
    score: Optional[Decimal] = None
    quantity_matched: Optional[Decimal] = None
    quantity_variance: Optional[Decimal] = None
    amount_matched: Optional[Decimal] = None
    amount_variance: Optional[Decimal] = None
    is_partial: Optional[bool] = None
    notes: Optional[str] = None


class MatchLineResponse(MatchLineBase):
    """Match line response schema."""
    id: UUID
    match_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BalanceLedgerResponse(BaseSchema):
    """Balance ledger response schema."""
    id: UUID
    po_id: Optional[UUID] = None
    invoice_id: Optional[UUID] = None
    delivery_note_id: Optional[UUID] = None
    match_id: UUID
    document_type: str
    original_amount: Decimal
    matched_amount: Decimal
    balance_remaining: Decimal
    original_quantity: Decimal
    matched_quantity: Decimal
    quantity_remaining: Decimal
    is_settled: bool
    settled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MatchBase(BaseSchema):
    """Base match schema."""
    invoice_id: UUID
    match_type: MatchType


class MatchCreate(MatchBase):
    """Match creation schema."""
    lines: list[MatchLineCreate] = Field(default_factory=list)


class MatchUpdate(BaseSchema):
    """Match update schema."""
    status: Optional[MatchStatus] = None
    decision: Optional[MatchDecision] = None
    overall_score: Optional[Decimal] = None
    notes: Optional[str] = None


class MatchResponse(MatchBase):
    """Match response schema."""
    id: UUID
    status: MatchStatus
    decision: MatchDecision
    overall_score: Decimal
    line_level_score: Decimal
    amount_score: Decimal
    date_score: Decimal
    invoice_total: Decimal
    po_total: Optional[Decimal] = None
    delivery_total: Optional[Decimal] = None
    variance_amount: Decimal
    variance_reason: Optional[str] = None
    confirmed_by_id: Optional[UUID] = None
    confirmed_at: Optional[datetime] = None
    rejected_by_id: Optional[UUID] = None
    rejected_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    lines: list[MatchLineResponse] = Field(default_factory=list)
    balance_entries: list[BalanceLedgerResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class MatchResultResponse(BaseSchema):
    """Complete match result with all related data."""
    match: MatchResponse
    invoice: InvoiceResponse
    purchase_order: Optional[PurchaseOrderResponse] = None
    delivery_note: Optional[DeliveryNoteResponse] = None


class ConfirmMatchRequest(BaseSchema):
    """Request to confirm a match."""
    match_id: UUID
    notes: Optional[str] = Field(None, max_length=1000)


class RejectMatchRequest(BaseSchema):
    """Request to reject a match."""
    match_id: UUID
    reason: str = Field(..., min_length=1, max_length=1000)
    notes: Optional[str] = Field(None, max_length=1000)


class MatchSummaryResponse(BaseSchema):
    """Summary statistics for matches."""
    total_matches: int
    pending_review: int
    auto_approved: int
    rejected: int
    total_variance: Decimal
    average_score: Decimal

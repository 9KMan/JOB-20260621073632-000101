# src/api/v1/schemas/matches.py
"""Match schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MatchBase(BaseModel):
    """Base match schema."""
    invoice_id: UUID
    delivery_note_id: Optional[UUID] = None
    purchase_order_id: Optional[UUID] = None


class MatchResponse(MatchBase):
    """Match response schema."""
    id: UUID
    line_level_score: Decimal
    amount_score: Decimal
    date_score: Decimal
    total_score: Decimal
    match_type: str
    status: str
    decision: Optional[str] = None
    quantity_variance: Decimal
    amount_variance: Decimal
    variance_reason: Optional[str] = None
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MatchCreate(MatchBase):
    """Match creation schema (for manual matching)."""
    pass


class MatchReview(BaseModel):
    """Match review schema."""
    decision: str = Field(..., pattern="^(confirmed|rejected)$")
    notes: Optional[str] = None


class MatchDecisionResponse(BaseModel):
    """Match decision response schema."""
    match_id: UUID
    decision: str
    status: str
    message: str


class MatchStatistics(BaseModel):
    """Match statistics schema."""
    total_matches: int
    pending: int
    confirmed: int
    rejected: int
    auto_approved: int
    human_review: int
    disputed: int
    average_score: Decimal


class MatchScoreBreakdown(BaseModel):
    """Match score breakdown schema."""
    line_level_score: Decimal
    amount_score: Decimal
    date_score: Decimal
    total_score: Decimal
    weights: dict[str, Decimal]


class MatchCandidate(BaseModel):
    """Match candidate for manual matching."""
    document_type: str  # invoice, delivery_note, purchase_order
    document_id: UUID
    document_number: str
    supplier_name: str
    total_amount: Decimal
    match_score: Decimal = Decimal("0.0000")
    match_type: str

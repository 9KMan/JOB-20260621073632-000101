"""Match schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.models.match import MatchDecision, MatchStatus


class MatchScoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    line_score: Decimal
    amount_score: Decimal
    date_score: Decimal
    composite_score: Decimal
    matched_skus: list[str] = Field(default_factory=list)
    unmatched_skus: list[str] = Field(default_factory=list)
    notes: str | None = None


class MatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    invoice_id: UUID
    purchase_order_id: UUID
    delivery_note_id: UUID | None
    status: MatchStatus
    decision: MatchDecision
    human_confirmed: bool
    human_decision: MatchDecision | None
    feedback_notes: str | None
    reviewed_by_id: UUID | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    score: MatchScoreRead | None = None


class MatchDecisionRequest(BaseModel):
    """Human reviewer input for a pending match."""

    decision: MatchDecision = Field(
        description="Reviewer decision. Must be APPROVED, REJECTED, or DISPUTE."
    )
    feedback_notes: str | None = Field(default=None, max_length=2048)

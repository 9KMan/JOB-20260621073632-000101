// src/app/schemas/match.py
"""Match Result schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MatchResultBase(BaseModel):
    """Base schema for match results."""

    match_type: str = Field(default="THREE_WAY")
    match_details: dict | None = None


class MatchResultCreate(MatchResultBase):
    """Schema for creating a match result."""

    invoice_id: UUID
    delivery_note_id: UUID | None = None
    po_id: UUID | None = None


class MatchResultUpdate(BaseModel):
    """Schema for updating a match result."""

    match_status: str | None = None
    decision_reason: str | None = None
    routing_decision: str | None = None
    confirmed_by: UUID | None = None


class MatchScore(BaseModel):
    """Schema for match scoring breakdown."""

    line_level_score: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    amount_score: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    date_score: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    overall_score: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))

    @property
    def weights(self) -> dict[str, Decimal]:
        """Return the weights used for scoring."""
        return {
            "line_level": Decimal("0.70"),
            "amount": Decimal("0.20"),
            "date": Decimal("0.10"),
        }


class MatchVariance(BaseModel):
    """Schema for match variance tracking."""

    quantity_variance: Decimal
    amount_variance: Decimal
    quantity_variance_percent: Decimal | None = None
    amount_variance_percent: Decimal | None = None


class MatchResultResponse(MatchResultBase):
    """Schema for match result response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    invoice_id: UUID
    delivery_note_id: UUID | None = None
    po_id: UUID | None = None
    line_level_score: Decimal
    amount_score: Decimal
    date_score: Decimal
    overall_score: Decimal
    match_status: str
    decision_reason: str | None = None
    routing_decision: str
    quantity_variance: Decimal
    amount_variance: Decimal
    is_confirmed: bool
    confirmed_by: UUID | None = None
    confirmed_at: date | None = None
    created_at: datetime
    updated_at: datetime

    @field_validator(
        "line_level_score", "amount_score", "date_score", "overall_score",
        "quantity_variance", "amount_variance",
        mode="before"
    )
    @classmethod
    def validate_decimals(cls, v: Decimal | None) -> Decimal:
        return v or Decimal("0.00")


class MatchResultWithDocuments(MatchResultResponse):
    """Schema for match result with related documents."""

    invoice_number: str | None = None
    po_number: str | None = None
    dn_number: str | None = None
    invoice_amount: Decimal | None = None
    po_amount: Decimal | None = None
    dn_amount: Decimal | None = None


class MatchConfirmationCreate(BaseModel):
    """Schema for creating a match confirmation."""

    confirmation_action: str = Field(pattern="^(APPROVE|REJECT|ADJUST)$")
    comments: str | None = None
    adjusted_score: Decimal | None = Field(default=None, ge=Decimal("0"), le=Decimal("1"))


class MatchConfirmationResponse(BaseModel):
    """Schema for match confirmation response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    match_id: UUID
    confirmed_by: UUID
    confirmation_action: str
    comments: str | None = None
    previous_score: Decimal | None = None
    adjusted_score: Decimal | None = None
    created_at: datetime


class MatchResultListResponse(BaseModel):
    """Schema for paginated match result list."""

    items: list[MatchResultResponse]
    total: int
    skip: int
    limit: int


class MatchSummary(BaseModel):
    """Schema for matching summary statistics."""

    total_matches: int
    auto_approved: int
    pending_review: int
    rejected: int
    average_score: Decimal
    match_rate: Decimal


class MatchDecisionRequest(BaseModel):
    """Request for match decision."""

    match_id: UUID
    decision: str = Field(pattern="^(APPROVE|REJECT|ESCALATE)$")
    reason: str | None = None
    notes: str | None = None


class MatchDecisionResponse(BaseModel):
    """Response for match decision."""

    match_id: UUID
    previous_status: str
    new_status: str
    routing_decision: str
    message: str


class CascadeMatchRequest(BaseModel):
    """Request for cascade matching."""

    invoice_id: UUID
    delivery_note_id: UUID | None = None
    po_id: UUID | None = None
    run_cascade: bool = True


class CascadeMatchResponse(BaseModel):
    """Response for cascade matching."""

    primary_match: MatchResultWithDocuments | None
    secondary_matches: list[MatchResultWithDocuments] = []
    balance_updates: list[dict] = []
    routing_decisions: list[dict] = []

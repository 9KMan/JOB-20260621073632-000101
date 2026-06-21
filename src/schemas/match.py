// src/schemas/match.py
"""Match schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from src.models.match import MatchStatus, MatchType
from src.schemas.common import BaseSchema, UUIDMixin


class MatchCreate(BaseModel):
    """Schema for creating a match record."""
    match_type: MatchType
    purchase_order_id: Optional[UUID] = None
    invoice_id: Optional[UUID] = None
    delivery_note_id: Optional[UUID] = None


class MatchUpdate(BaseModel):
    """Schema for updating a match record."""
    status: Optional[MatchStatus] = None
    resolution_notes: Optional[str] = None


class MatchDecision(BaseModel):
    """Schema for making a match decision."""
    decision: MatchStatus = Field(
        description="Decision: CONFIRMED, REJECTED, or HUMAN_REVIEW"
    )
    notes: Optional[str] = None


class MatchResponse(UUIDMixin, BaseSchema):
    """Response schema for match records."""
    match_type: MatchType
    status: MatchStatus
    total_score: Decimal
    line_level_score: Decimal
    amount_score: Decimal
    date_score: Decimal
    matched_amount: Decimal
    variance_amount: Decimal
    quantity_variance: Optional[Decimal]
    price_variance: Optional[Decimal]
    date_variance_days: Optional[int]
    purchase_order_id: Optional[UUID]
    invoice_id: Optional[UUID]
    delivery_note_id: Optional[UUID]
    resolved_by: Optional[UUID]
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]
    line_matches: Optional[dict]
    created_at: datetime
    updated_at: datetime


class MatchSummaryResponse(BaseSchema):
    """Summary response for match listings."""
    id: UUID
    match_type: MatchType
    status: MatchStatus
    total_score: Decimal
    matched_amount: Decimal
    purchase_order_id: Optional[UUID]
    invoice_id: Optional[UUID]
    delivery_note_id: Optional[UUID]
    created_at: datetime


class MatchResultResponse(BaseModel):
    """Response schema for match results with full details."""
    match: MatchResponse
    invoice_number: Optional[str] = None
    po_number: Optional[str] = None
    dn_number: Optional[str] = None
    decision: str
    message: str

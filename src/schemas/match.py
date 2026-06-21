// src/schemas/match.py
"""Match schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.base import PaginatedResponse


class MatchLineResponse(BaseModel):
    """Schema for Match line response."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    match_id: UUID
    po_line_id: Optional[UUID] = None
    invoice_line_id: Optional[UUID] = None
    delivery_note_line_id: Optional[UUID] = None
    sku_match: bool
    quantity_match: bool
    price_match: bool
    po_quantity: Optional[Decimal] = None
    invoice_quantity: Optional[Decimal] = None
    delivery_quantity: Optional[Decimal] = None
    matched_quantity: Decimal
    po_amount: Optional[Decimal] = None
    invoice_amount: Optional[Decimal] = None
    matched_amount: Decimal
    variance: Decimal
    variance_reason: Optional[str] = None
    created_at: datetime


class MatchConfirmationCreate(BaseModel):
    """Schema for creating a match confirmation."""

    decision: str = Field(..., pattern="^(approved|rejected)$")
    notes: Optional[str] = None


class MatchConfirmationResponse(BaseModel):
    """Schema for match confirmation response."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    match_id: UUID
    confirmed_by: UUID
    decision: str
    notes: Optional[str] = None
    confirmed_at: datetime


class MatchResponse(BaseModel):
    """Schema for Match response."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    invoice_id: UUID
    delivery_note_id: Optional[UUID] = None
    purchase_order_id: Optional[UUID] = None
    line_score: Decimal
    amount_score: Decimal
    date_score: Decimal
    total_score: Decimal
    confidence_level: str
    invoice_amount: Decimal
    po_amount: Decimal
    variance: Decimal
    matched_amount: Decimal
    status: str
    decision: str
    match_type: str
    notes: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    confirmed_by: Optional[UUID] = None
    lines: list[MatchLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class MatchDecisionRequest(BaseModel):
    """Schema for making a match decision."""

    decision: str = Field(..., pattern="^(approved|rejected)$")
    notes: Optional[str] = None


class MatchListResponse(PaginatedResponse[MatchResponse]):
    """Paginated list of Matches."""

    pass


class MatchSummaryResponse(BaseModel):
    """Summary of matches by status."""

    total: int
    confirmed: int
    pending: int
    rejected: int
    auto_approved: int
    human_review: int
    disputed: int

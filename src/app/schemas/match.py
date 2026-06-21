// src/app/schemas/match.py
"""Match schemas."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict


class MatchLineBase(BaseModel):
    """Base schema for Match line."""

    po_line_id: Optional[uuid.UUID] = None
    invoice_line_id: Optional[uuid.UUID] = None
    dn_line_id: Optional[uuid.UUID] = None
    product_match_score: Decimal = Decimal("0.0000")
    quantity_match_score: Decimal = Decimal("0.0000")
    price_match_score: Decimal = Decimal("0.0000")
    line_total_score: Decimal = Decimal("0.0000")
    po_quantity: Optional[Decimal] = None
    invoice_quantity: Optional[Decimal] = None
    dn_quantity: Optional[Decimal] = None
    quantity_variance: Decimal = Decimal("0.0000")
    po_line_total: Optional[Decimal] = None
    invoice_line_total: Optional[Decimal] = None
    dn_line_total: Optional[Decimal] = None
    amount_variance: Decimal = Decimal("0.00")
    metadata: Optional[dict] = None


class MatchLineCreate(MatchLineBase):
    """Schema for creating a Match line."""

    match_id: uuid.UUID


class MatchLineResponse(MatchLineBase):
    """Schema for Match line response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    match_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class MatchBase(BaseModel):
    """Base schema for Match."""

    purchase_order_id: Optional[uuid.UUID] = None
    invoice_id: Optional[uuid.UUID] = None
    delivery_note_id: Optional[uuid.UUID] = None
    match_type: str
    match_score: Decimal = Decimal("0.0000")
    notes: Optional[str] = None
    metadata: Optional[dict] = None


class MatchCreate(MatchBase):
    """Schema for creating a Match."""

    lines: List[MatchLineCreate] = Field(default_factory=list)


class MatchUpdate(BaseModel):
    """Schema for updating a Match."""

    decision: Optional[str] = None
    notes: Optional[str] = None
    dispute_reason: Optional[str] = None
    metadata: Optional[dict] = None


class MatchDecisionUpdate(BaseModel):
    """Schema for updating match decision."""

    decision: str = Field(..., description="AUTO_APPROVED, HUMAN_REVIEW, REJECTED, or DISPUTED")
    notes: Optional[str] = None
    dispute_reason: Optional[str] = None


class MatchResponse(MatchBase):
    """Schema for Match response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    line_level_score: Decimal
    amount_score: Decimal
    date_score: Decimal
    po_amount: Decimal
    invoice_amount: Decimal
    dn_amount: Decimal
    variance_amount: Decimal
    decision: str
    confirmed_by_id: Optional[uuid.UUID] = None
    confirmed_at: Optional[datetime] = None
    lines: List[MatchLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class MatchListResponse(BaseModel):
    """Schema for paginated Match list."""

    items: List[MatchResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class MatchScoreSummary(BaseModel):
    """Summary of match scores."""

    total_score: Decimal
    line_level_score: Decimal
    amount_score: Decimal
    date_score: Decimal
    matched_lines: int
    total_lines: int
    matched_amount: Decimal
    variance_amount: Decimal


class ThreeWayMatchRequest(BaseModel):
    """Request for 3-way matching."""

    invoice_id: uuid.UUID
    delivery_note_ids: List[uuid.UUID] = Field(default_factory=list)
    po_reference: Optional[str] = None
    auto_match: bool = Field(default=True, description="Whether to auto-create matches")


class ThreeWayMatchResponse(BaseModel):
    """Response for 3-way matching."""

    matches: List[MatchResponse]
    unmatched_invoices: List[uuid.UUID] = Field(default_factory=list)
    unmatched_delivery_notes: List[uuid.UUID] = Field(default_factory=list)
    summary: MatchScoreSummary

// src/schemas/match.py
"""Match schemas for 3-way matching."""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import ConfigDict, Field

from src.schemas.common import BaseSchema, PaginatedResponse


class MatchLineBase(BaseSchema):
    """Base schema for match line items."""

    po_line_id: Optional[UUID] = None
    invoice_line_id: Optional[UUID] = None
    dn_line_id: Optional[UUID] = None
    product_code: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    po_quantity: Optional[Decimal] = None
    invoice_quantity: Optional[Decimal] = None
    dn_quantity: Optional[Decimal] = None
    matched_quantity: Decimal = Field(default=Decimal("0"), ge=0)
    quantity_variance: Decimal = Field(default=Decimal("0"))
    unit_price: Decimal = Field(..., ge=0)
    line_amount: Decimal = Field(default=Decimal("0"), ge=0)
    variance_amount: Decimal = Field(default=Decimal("0"))
    is_matched: bool = Field(default=False)
    match_confidence: Optional[Decimal] = None
    notes: Optional[str] = None


class MatchLineCreate(MatchLineBase):
    """Schema for creating match line items."""

    pass


class MatchLineUpdate(BaseSchema):
    """Schema for updating match line items."""

    po_line_id: Optional[UUID] = None
    invoice_line_id: Optional[UUID] = None
    dn_line_id: Optional[UUID] = None
    matched_quantity: Optional[Decimal] = Field(None, ge=0)
    quantity_variance: Optional[Decimal] = None
    line_amount: Optional[Decimal] = Field(None, ge=0)
    variance_amount: Optional[Decimal] = None
    is_matched: Optional[bool] = None
    match_confidence: Optional[Decimal] = None
    notes: Optional[str] = None


class MatchLineResponse(MatchLineBase):
    """Schema for match line item responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    match_id: UUID
    created_at: datetime
    updated_at: datetime


class MatchBase(BaseSchema):
    """Base schema for Matches."""

    invoice_id: UUID
    purchase_order_id: Optional[UUID] = None
    delivery_note_id: Optional[UUID] = None
    status: str = Field(default="pending", max_length=20)
    decision: str = Field(default="human_review", max_length=20)
    match_type: str = Field(..., max_length=30)
    line_level_score: Optional[Decimal] = None
    amount_score: Optional[Decimal] = None
    date_score: Optional[Decimal] = None
    total_score: Optional[Decimal] = None
    invoice_amount: Decimal = Field(..., ge=0)
    po_amount: Optional[Decimal] = None
    dn_amount: Optional[Decimal] = None
    variance_amount: Decimal = Field(default=Decimal("0"))
    variance_percentage: Optional[Decimal] = None
    is_variance_within_tolerance: bool = Field(default=True)
    variance_tolerance_percentage: Decimal = Field(default=Decimal("5.00"))
    line_matches: int = Field(default=0, ge=0)
    line_total: int = Field(default=0, ge=0)
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    confirmed_by: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    notes: Optional[str] = None


class MatchCreate(MatchBase):
    """Schema for creating Matches."""

    lines: List[MatchLineCreate] = Field(default_factory=list)


class MatchUpdate(BaseSchema):
    """Schema for updating Matches."""

    status: Optional[str] = Field(None, max_length=20)
    decision: Optional[str] = Field(None, max_length=20)
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    confirmed_by: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    notes: Optional[str] = None


class MatchResponse(MatchBase):
    """Schema for Match responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
    lines: List[MatchLineResponse] = Field(default_factory=list)


class MatchListResponse(PaginatedResponse[MatchResponse]):
    """Schema for paginated Match list response."""

    pass


class MatchConfirmRequest(BaseSchema):
    """Schema for confirming a match."""

    reviewed_by: str = Field(..., max_length=255, description="User confirming the match")
    review_notes: Optional[str] = Field(None, description="Optional notes for confirmation")


class MatchRejectRequest(BaseSchema):
    """Schema for rejecting a match."""

    reviewed_by: str = Field(..., max_length=255, description="User rejecting the match")
    review_notes: str = Field(..., description="Required notes explaining rejection")


class MatchSummary(BaseSchema):
    """Schema for Match summary (minimal data)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    invoice_id: UUID
    purchase_order_id: Optional[UUID] = None
    delivery_note_id: Optional[UUID] = None
    status: str
    decision: str
    match_type: str
    total_score: Optional[Decimal] = None
    variance_amount: Decimal
    is_variance_within_tolerance: bool


class MatchResult(BaseSchema):
    """Schema for matching result."""

    match_id: Optional[UUID] = None
    invoice_id: UUID
    purchase_order_id: Optional[UUID] = None
    delivery_note_id: Optional[UUID] = None
    match_type: str
    status: str
    decision: str
    line_level_score: Optional[Decimal] = None
    amount_score: Optional[Decimal] = None
    date_score: Optional[Decimal] = None
    total_score: Optional[Decimal] = None
    variance_amount: Decimal
    variance_percentage: Optional[Decimal] = None
    is_variance_within_tolerance: bool
    line_matches: int
    line_total: int
    lines: List[MatchLineResponse] = Field(default_factory=list)

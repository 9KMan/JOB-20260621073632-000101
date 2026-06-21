// src/schemas/matching.py
"""Matching schemas."""
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import Field

from src.schemas.base import BaseSchema, TimestampUUIDSchema
from src.models.enums import MatchStatus, MatchType, BalanceType


class MatchScoreBase(BaseSchema):
    """Base match score schema."""
    
    po_line_id: Optional[UUID] = None
    invoice_line_id: Optional[UUID] = None
    dn_line_id: Optional[UUID] = None
    product_code_match: bool = False
    product_match_score: Decimal = Decimal("0.0000")
    po_quantity: Optional[Decimal] = None
    invoice_quantity: Optional[Decimal] = None
    dn_quantity: Optional[Decimal] = None
    quantity_match_score: Decimal = Decimal("0.0000")
    po_unit_price: Optional[Decimal] = None
    invoice_unit_price: Optional[Decimal] = None
    price_match_score: Decimal = Decimal("0.0000")
    po_line_amount: Optional[Decimal] = None
    invoice_line_amount: Optional[Decimal] = None
    dn_line_amount: Optional[Decimal] = None
    line_amount_variance: Decimal = Decimal("0.00")
    line_score: Decimal = Decimal("0.0000")


class MatchScoreResponse(MatchScoreBase):
    """Schema for match score response."""
    
    id: UUID
    match_id: UUID


class MatchBase(BaseSchema):
    """Base match schema."""
    
    po_id: Optional[UUID] = None
    invoice_id: Optional[UUID] = None
    dn_id: Optional[UUID] = None
    match_type: MatchType


class MatchCreate(MatchBase):
    """Schema for creating a match."""
    
    pass


class MatchUpdate(BaseSchema):
    """Schema for updating a match."""
    
    status: Optional[MatchStatus] = None
    review_notes: Optional[str] = None


class MatchResponse(TimestampUUIDSchema):
    """Schema for match response."""
    
    po_id: Optional[UUID] = None
    invoice_id: Optional[UUID] = None
    dn_id: Optional[UUID] = None
    match_type: MatchType
    status: MatchStatus
    overall_score: Decimal
    line_level_score: Decimal
    amount_score: Decimal
    date_score: Decimal
    invoice_amount: Optional[Decimal] = None
    po_amount: Optional[Decimal] = None
    dn_amount: Optional[Decimal] = None
    variance_amount: Decimal
    variance_reason: Optional[str] = None
    review_notes: Optional[str] = None
    confirmed_by_id: Optional[UUID] = None
    confirmed_at: Optional[datetime] = None
    rejected_by_id: Optional[UUID] = None
    rejected_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    match_scores: List[MatchScoreResponse] = []


class MatchReview(BaseSchema):
    """Schema for reviewing a match."""
    
    status: MatchStatus = Field(..., description="CONFIRMED or REJECTED")
    review_notes: Optional[str] = Field(None, max_length=1000)
    rejection_reason: Optional[str] = Field(None, max_length=1000)


class BalanceEntryBase(BaseSchema):
    """Base balance entry schema."""
    
    po_id: Optional[UUID] = None
    invoice_id: Optional[UUID] = None
    dn_id: Optional[UUID] = None
    balance_type: BalanceType
    original_amount: Decimal
    matched_amount: Decimal = Decimal("0.00")
    remaining_amount: Decimal


class BalanceEntryResponse(TimestampUUIDSchema):
    """Schema for balance entry response."""
    
    po_id: Optional[UUID] = None
    invoice_id: Optional[UUID] = None
    dn_id: Optional[UUID] = None
    balance_type: BalanceType
    original_amount: Decimal
    matched_amount: Decimal
    remaining_amount: Decimal
    match_id: Optional[UUID] = None
    po_line_id: Optional[UUID] = None
    invoice_line_id: Optional[UUID] = None
    dn_line_id: Optional[UUID] = None
    is_settled: bool
    settled_at: Optional[datetime] = None


class MatchResult(BaseSchema):
    """Schema for match result summary."""
    
    match_id: Optional[UUID] = None
    po_id: UUID
    invoice_id: Optional[UUID] = None
    dn_id: Optional[UUID] = None
    status: MatchStatus
    overall_score: Decimal
    line_level_score: Decimal
    amount_score: Decimal
    date_score: Decimal
    variance_amount: Decimal
    variance_reason: Optional[str] = None
    action: str = Field(..., description="AUTO_APPROVE, HUMAN_REVIEW, or DISPUTE")
    match_scores: List[MatchScoreResponse] = []


class MatchResultList(BaseSchema):
    """Schema for list of match results."""
    
    matches: List[MatchResult]
    total_matches: int
    auto_approved: int
    pending_review: int
    rejected: int

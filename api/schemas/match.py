// api/schemas/match.py
"""Match Pydantic schemas."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MatchScoreBreakdown(BaseModel):
    """Score breakdown for a match."""
    
    line_level_score: Optional[Decimal] = None
    amount_score: Optional[Decimal] = None
    date_score: Optional[Decimal] = None
    overall_confidence: Decimal


class MatchLineResponse(BaseModel):
    """Schema for Match line item response."""
    
    id: UUID
    match_id: UUID
    invoice_line_id: UUID
    po_line_id: Optional[UUID] = None
    delivery_note_line_id: Optional[UUID] = None
    line_confidence_score: Decimal
    quantity_matched: Decimal
    quantity_invoice: Decimal
    quantity_po: Optional[Decimal] = None
    quantity_dn: Optional[Decimal] = None
    quantity_variance: Decimal
    amount_matched: Decimal
    amount_invoice: Decimal
    amount_po: Optional[Decimal] = None
    amount_dn: Optional[Decimal] = None
    amount_variance: Decimal
    item_code_match: bool
    description_similarity: Optional[Decimal] = None
    quantity_match: bool
    price_match: bool
    notes: Optional[str] = None
    is_perfect_match: bool
    
    model_config = {"from_attributes": True}


class MatchBase(BaseModel):
    """Base schema for Matches."""
    
    invoice_id: UUID
    delivery_note_id: Optional[UUID] = None
    purchase_order_id: UUID


class MatchCreate(MatchBase):
    """Schema for creating a Match."""
    
    pass


class MatchUpdate(BaseModel):
    """Schema for updating a Match."""
    
    status: Optional[str] = None
    decision: Optional[str] = None
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None


class MatchDecisionRequest(BaseModel):
    """Schema for making a match decision."""
    
    decision: str = Field(
        description="Decision: auto_approved, human_review, dispute, partially_matched"
    )
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None


class MatchResponse(MatchBase):
    """Schema for Match response."""
    
    id: UUID
    match_type: str
    overall_confidence_score: Decimal
    line_level_score: Optional[Decimal] = None
    amount_score: Optional[Decimal] = None
    date_score: Optional[Decimal] = None
    invoice_amount: Decimal
    po_amount: Decimal
    dn_amount: Optional[Decimal] = None
    variance_amount: Decimal
    variance_percent: Decimal
    status: str
    decision: Optional[str] = None
    matched_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[UUID] = None
    is_auto_matched: bool
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    is_confirmed: bool
    is_pending: bool
    is_rejected: bool
    
    model_config = {"from_attributes": True}


class MatchDetailResponse(MatchResponse):
    """Schema for detailed Match response with line items."""
    
    lines: List[MatchLineResponse] = []
    score_breakdown: Optional[MatchScoreBreakdown] = None
    
    model_config = {"from_attributes": True}


class MatchListResponse(BaseModel):
    """Schema for paginated list of Matches."""
    
    items: List[MatchResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class MatchSummaryResponse(BaseModel):
    """Summary of matching results."""
    
    total_matches: int
    confirmed_count: int
    pending_count: int
    rejected_count: int
    partial_count: int
    auto_approved_count: int
    human_review_count: int
    dispute_count: int
    average_confidence_score: Optional[Decimal] = None
    high_confidence_matches: int
    medium_confidence_matches: int
    low_confidence_matches: int

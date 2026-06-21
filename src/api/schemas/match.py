// src/api/schemas/match.py
from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from src.models.match import MatchStatus, MatchDecision, MatchType


class MatchLineDetail(BaseModel):
    """Line-level match detail."""
    po_line_id: Optional[UUID] = None
    invoice_line_id: Optional[UUID] = None
    dn_line_id: Optional[UUID] = None
    score: Decimal
    quantity_match: bool
    amount_match: bool


class MatchBase(BaseModel):
    """Base match schema."""
    match_type: MatchType
    invoice_id: Optional[UUID] = None
    delivery_note_id: Optional[UUID] = None
    purchase_order_id: Optional[UUID] = None


class MatchCreate(MatchBase):
    """Match creation schema."""
    total_score: Decimal
    line_level_score: Optional[Decimal] = None
    amount_score: Optional[Decimal] = None
    date_score: Optional[Decimal] = None
    po_amount: Optional[Decimal] = None
    invoice_amount: Optional[Decimal] = None
    dn_amount: Optional[Decimal] = None
    variance_amount: Optional[Decimal] = None
    po_quantity: Optional[Decimal] = None
    invoice_quantity: Optional[Decimal] = None
    dn_quantity: Optional[Decimal] = None
    quantity_variance: Optional[Decimal] = None
    line_level_details: Optional[Dict[str, Any]] = None


class MatchReviewRequest(BaseModel):
    """Match review request schema."""
    decision: MatchDecision
    notes: Optional[str] = None


class MatchResponse(MatchBase):
    """Match response schema."""
    id: UUID
    total_score: Decimal
    line_level_score: Optional[Decimal] = None
    amount_score: Optional[Decimal] = None
    date_score: Optional[Decimal] = None
    po_amount: Optional[Decimal] = None
    invoice_amount: Optional[Decimal] = None
    dn_amount: Optional[Decimal] = None
    variance_amount: Optional[Decimal] = None
    status: MatchStatus
    decision: Optional[MatchDecision] = None
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    line_level_details: Optional[Dict[str, Any]] = None
    match_confidence: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MatchListResponse(BaseModel):
    """Match list response schema."""
    items: List[MatchResponse]
    total: int
    page: int
    page_size: int


class MatchSummary(BaseModel):
    """Summary of matches for a document."""
    document_type: str
    document_id: UUID
    document_number: str
    total_matches: int
    auto_approved: int
    pending_review: int
    rejected: int

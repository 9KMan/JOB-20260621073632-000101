// src/schemas/matching.py
"""
Matching Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from decimal import Decimal

from src.schemas.common import TimestampMixin, UUIDMixin


class MatchRecordBase(BaseModel):
    """Base schema for Match Record"""
    purchase_order_id: UUID
    invoice_id: Optional[UUID] = None
    delivery_note_id: Optional[UUID] = None


class MatchRecordResponse(MatchRecordBase, UUIDMixin, TimestampMixin):
    """Response schema for Match Record"""
    match_status: str
    decision: Optional[str] = None
    line_match_score: Decimal
    amount_match_score: Decimal
    date_match_score: Decimal
    overall_score: Decimal
    match_type: str
    amount_variance: Decimal
    quantity_variance: Decimal
    variance_reason: Optional[str] = None
    line_match_details: Optional[Dict[str, Any]] = None
    match_notes: Optional[str] = None
    confirmed_by: Optional[UUID] = None
    confirmed_at: Optional[datetime] = None
    review_comments: Optional[str] = None
    
    class Config:
        from_attributes = True


class MatchRecordListResponse(BaseModel):
    """Response schema for listing Match Records"""
    items: List[MatchRecordResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class MatchConfirmRequest(BaseModel):
    """Request schema for confirming a match"""
    match_status: str = Field(..., description="confirmed or rejected")
    review_comments: Optional[str] = None


class MatchScoreBreakdown(BaseModel):
    """Detailed match score breakdown"""
    line_score: Decimal
    amount_score: Decimal
    date_score: Decimal
    overall_score: Decimal
    line_match_percentage: Decimal
    amount_match_percentage: Decimal


class MatchVarianceDetail(BaseModel):
    """Detail of variance between documents"""
    amount_variance: Decimal
    amount_variance_percentage: Decimal
    quantity_variance: Decimal
    quantity_variance_percentage: Decimal
    variance_reason: str


class MatchDetailResponse(BaseModel):
    """Detailed match response with breakdown"""
    match_record: MatchRecordResponse
    score_breakdown: MatchScoreBreakdown
    variance_detail: MatchVarianceDetail
    purchase_order_summary: Optional[Dict[str, Any]] = None
    invoice_summary: Optional[Dict[str, Any]] = None
    delivery_note_summary: Optional[Dict[str, Any]] = None


class BalanceLedgerResponse(UUIDMixin, TimestampMixin):
    """Response schema for Balance Ledger"""
    document_type: str
    document_id: UUID
    purchase_order_id: UUID
    original_amount: Decimal
    matched_amount: Decimal
    balance_amount: Decimal
    match_record_id: Optional[UUID] = None
    status: str
    
    class Config:
        from_attributes = True


class MatchLearningHistoryResponse(UUIDMixin, TimestampMixin):
    """Response schema for Match Learning History"""
    match_record_id: UUID
    original_match_status: str
    confirmed_match_status: str
    confirmed_by: UUID
    confirmed_at: datetime
    feedback_type: Optional[str] = None
    feedback_notes: Optional[str] = None
    po_number: Optional[str] = None
    invoice_number: Optional[str] = None
    dn_number: Optional[str] = None
    
    class Config:
        from_attributes = True


class MatchSummaryResponse(BaseModel):
    """Summary of matching results"""
    total_matches: int
    confirmed_matches: int
    pending_matches: int
    rejected_matches: int
    auto_approved: int
    human_review_required: int
    dispute_count: int
    average_match_score: Decimal

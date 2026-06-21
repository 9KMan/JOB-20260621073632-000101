// src/app/schemas/match.py
"""Match schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MatchRequest(BaseModel):
    """Request to match documents."""
    
    invoice_id: Optional[str] = None
    delivery_note_id: Optional[str] = None
    purchase_order_id: Optional[str] = None
    match_type: Optional[str] = None  # If None, auto-detect best match type
    
    force_match: bool = False  # Force match even with variances


class MatchCriteria(BaseModel):
    """Matching criteria weights."""
    
    line_match_weight: Decimal = Field(default=Decimal("0.70"))
    amount_match_weight: Decimal = Field(default=Decimal("0.20"))
    date_match_weight: Decimal = Field(default=Decimal("0.10"))
    date_tolerance_days: int = 7
    amount_tolerance_percent: Decimal = Field(default=Decimal("5.0"))


class LineMatchDetail(BaseModel):
    """Line-level match detail."""
    
    po_line_id: Optional[str] = None
    invoice_line_id: Optional[str] = None
    dn_line_id: Optional[str] = None
    product_code_match: bool
    quantity_match: bool
    quantity_variance: Decimal
    amount_variance: Decimal
    score: Decimal


class MatchResponse(BaseModel):
    """Match operation response."""
    
    success: bool
    message: str
    match_record: Optional["MatchRecordResponse"] = None
    decision: str
    alternative_matches: list["MatchRecordResponse"] = []


class MatchRecordResponse(BaseModel):
    """Match record response schema."""
    
    id: str
    invoice_id: Optional[str] = None
    delivery_note_id: Optional[str] = None
    purchase_order_id: Optional[str] = None
    
    match_type: str
    overall_score: Decimal
    line_match_score: Decimal
    amount_match_score: Decimal
    date_match_score: Decimal
    
    quantity_variance: Decimal
    amount_variance: Decimal
    
    status: str
    decision: str
    
    variance_reason: Optional[str] = None
    review_notes: Optional[str] = None
    
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class MatchReviewRequest(BaseModel):
    """Request to review/confirm a match."""
    
    match_id: str
    decision: str = Field(description="confirm, reject, or override")
    review_notes: Optional[str] = None


class MatchDecisionResponse(BaseModel):
    """Match decision response."""
    
    success: bool
    match_id: str
    previous_status: str
    new_status: str
    decision: str
    message: str


class MatchSummaryResponse(BaseModel):
    """Summary of matches for a document."""
    
    document_type: str
    document_id: str
    document_number: str
    total_matches: int
    confirmed_matches: int
    pending_matches: int
    rejected_matches: int
    average_score: Decimal


class MatchStatistics(BaseModel):
    """Overall matching statistics."""
    
    total_matches: int
    auto_approved: int
    pending_review: int
    rejected: int
    average_score: Decimal
    average_resolution_time_hours: Optional[Decimal] = None

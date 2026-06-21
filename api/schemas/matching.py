// api/schemas/matching.py
"""Matching schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


class MatchingLineResponse(BaseModel):
    """Schema for matching line response."""
    
    id: UUID
    matching_record_id: UUID
    po_line_id: Optional[UUID]
    invoice_line_id: Optional[UUID]
    dn_line_id: Optional[UUID]
    po_quantity: Optional[Decimal]
    invoice_quantity: Optional[Decimal]
    dn_quantity: Optional[Decimal]
    matched_quantity: Decimal
    variance_quantity: Decimal
    po_amount: Optional[Decimal]
    invoice_amount: Optional[Decimal]
    dn_amount: Optional[Decimal]
    matched_amount: Decimal
    variance_amount: Decimal
    is_matched: bool
    match_confidence: Decimal
    description_similarity: Decimal
    item_code_match: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class MatchingRecordBase(BaseModel):
    """Base matching record schema."""
    
    po_id: Optional[UUID] = None
    invoice_id: Optional[UUID] = None
    dn_id: Optional[UUID] = None


class MatchingRecordCreate(MatchingRecordBase):
    """Schema for creating a matching record."""
    pass


class MatchingRecordResponse(BaseModel):
    """Schema for matching record response."""
    
    id: UUID
    po_id: Optional[UUID]
    invoice_id: Optional[UUID]
    dn_id: Optional[UUID]
    match_type: str
    status: str
    decision: Optional[str]
    match_score: Decimal
    po_amount: Optional[Decimal]
    invoice_amount: Optional[Decimal]
    dn_amount: Optional[Decimal]
    variance_amount: Decimal
    variance_percentage: Decimal
    invoice_date_match: bool
    delivery_date_match: bool
    date_variance_days: int
    line_level_score: Decimal
    amount_score: Decimal
    date_score: Decimal
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class MatchingRecordDetailResponse(MatchingRecordResponse):
    """Schema for detailed matching record response with lines."""
    
    lines: List[MatchingLineResponse] = []
    
    model_config = {"from_attributes": True}


class MatchingDecisionRequest(BaseModel):
    """Schema for confirming/rejecting a matching decision."""
    
    decision: str = Field(..., description="auto_approve, human_review, or dispute")
    review_notes: Optional[str] = None


class MatchScoreResponse(BaseModel):
    """Schema for match score breakdown."""
    
    overall_score: Decimal
    line_level_score: Decimal
    amount_score: Decimal
    date_score: Decimal
    invoice_date_match: bool
    delivery_date_match: bool
    date_variance_days: int
    auto_approve: bool
    needs_human_review: bool
    rejection_reason: Optional[str] = None


class MatchRequest(BaseModel):
    """Schema for requesting a match."""
    
    invoice_id: Optional[UUID] = None
    dn_id: Optional[UUID] = None
    po_id: Optional[UUID] = None
    match_type: str = Field(..., description="po_invoice, po_dn, invoice_dn, or three_way")

// src/app/schemas/match.py
"""Match Pydantic schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class MatchLineBase(BaseModel):
    """Base match line schema."""
    invoice_line_id: Optional[UUID] = None
    dn_line_id: Optional[UUID] = None
    po_line_id: Optional[UUID] = None
    quantity_invoice: Decimal
    quantity_po: Decimal
    quantity_dn: Decimal


class MatchLineCreate(MatchLineBase):
    """Match line creation schema."""
    pass


class MatchLineUpdate(BaseModel):
    """Match line update schema."""
    quantity_matched: Optional[Decimal] = None


class MatchLineResponse(MatchLineBase):
    """Match line response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    match_id: UUID
    match_score: Decimal
    quantity_matched: Decimal
    amount_matched: Decimal
    amount_invoice: Decimal
    amount_po: Decimal
    amount_dn: Decimal
    variance_amount: Decimal
    created_at: datetime
    updated_at: datetime


class MatchBase(BaseModel):
    """Base match schema."""
    invoice_id: UUID
    delivery_note_id: Optional[UUID] = None
    purchase_order_id: Optional[UUID] = None
    match_type: str = Field(..., max_length=20)


class MatchCreate(MatchBase):
    """Match creation schema."""
    lines: Optional[List[MatchLineCreate]] = None


class MatchUpdate(BaseModel):
    """Match update schema."""
    status: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = None


class MatchDecisionUpdate(BaseModel):
    """Match decision update schema."""
    decision: str = Field(..., max_length=20)
    notes: Optional[str] = None


class MatchResponse(MatchBase):
    """Match response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    status: str
    decision: str
    line_match_score: Decimal
    amount_match_score: Decimal
    date_match_score: Decimal
    overall_score: Decimal
    invoice_amount: Decimal
    po_amount: Decimal
    dn_amount: Decimal
    matched_amount: Decimal
    variance_amount: Decimal
    price_variance: Decimal
    quantity_variance: Decimal
    date_variance_days: int
    notes: Optional[str] = None
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    lines: List[MatchLineResponse] = []
    created_at: datetime
    updated_at: datetime


class MatchSummary(BaseModel):
    """Match summary for dashboard."""
    total_matches: int
    pending: int
    confirmed: int
    rejected: int
    disputed: int
    auto_approved: int
    human_review: int

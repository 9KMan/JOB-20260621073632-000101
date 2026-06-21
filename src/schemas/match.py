// src/schemas/match.py
"""Match schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MatchLineBase(BaseModel):
    """Base match line schema."""
    
    item_code: str
    description: Optional[str] = None
    po_quantity: Optional[Decimal] = None
    invoice_quantity: Optional[Decimal] = None
    delivery_quantity: Optional[Decimal] = None
    po_unit_price: Optional[Decimal] = None
    invoice_unit_price: Optional[Decimal] = None
    quantity_match_score: Decimal = Field(default=Decimal("0.0000"))
    price_match_score: Decimal = Field(default=Decimal("0.0000"))
    quantity_variance: Decimal = Field(default=Decimal("0.000"))
    price_variance: Decimal = Field(default=Decimal("0.0000"))
    po_line_total: Optional[Decimal] = None
    invoice_line_total: Optional[Decimal] = None
    is_matched: bool = False
    variance_reason: Optional[str] = None


class MatchLineCreate(MatchLineBase):
    """Match line creation schema."""
    
    po_line_id: Optional[UUID] = None
    invoice_line_id: Optional[UUID] = None
    delivery_line_id: Optional[UUID] = None


class MatchLineResponse(BaseModel):
    """Match line response schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    match_id: UUID
    po_line_id: Optional[UUID] = None
    invoice_line_id: Optional[UUID] = None
    delivery_line_id: Optional[UUID] = None
    item_code: str
    description: Optional[str] = None
    po_quantity: Optional[Decimal] = None
    invoice_quantity: Optional[Decimal] = None
    delivery_quantity: Optional[Decimal] = None
    po_unit_price: Optional[Decimal] = None
    invoice_unit_price: Optional[Decimal] = None
    quantity_match_score: Decimal
    price_match_score: Decimal
    quantity_variance: Decimal
    price_variance: Decimal
    po_line_total: Optional[Decimal] = None
    invoice_line_total: Optional[Decimal] = None
    is_matched: bool
    variance_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class MatchBase(BaseModel):
    """Base match schema."""
    
    match_type: str
    purchase_order_id: Optional[UUID] = None
    invoice_id: Optional[UUID] = None
    delivery_note_id: Optional[UUID] = None


class MatchCreate(MatchBase):
    """Match creation schema."""
    
    lines: List[MatchLineCreate] = Field(default_factory=list)


class MatchUpdate(BaseModel):
    """Match update schema."""
    
    decision: Optional[str] = None
    review_notes: Optional[str] = None


class MatchReviewRequest(BaseModel):
    """Match review request schema."""
    
    decision: str = Field(..., pattern="^(confirmed|rejected)$")
    review_notes: Optional[str] = None


class MatchResponse(BaseModel):
    """Match response schema."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    match_type: str
    decision: str
    purchase_order_id: Optional[UUID] = None
    invoice_id: Optional[UUID] = None
    delivery_note_id: Optional[UUID] = None
    overall_score: Decimal
    line_level_score: Decimal
    amount_score: Decimal
    date_score: Decimal
    po_amount: Optional[Decimal] = None
    invoice_amount: Optional[Decimal] = None
    delivery_amount: Optional[Decimal] = None
    variance_amount: Decimal
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    processing_notes: Optional[str] = None
    auto_approved: bool
    created_at: datetime
    updated_at: datetime
    lines: List[MatchLineResponse] = Field(default_factory=list)


class MatchSummary(BaseModel):
    """Match summary for dashboard."""
    
    total_matches: int
    confirmed: int
    pending: int
    rejected: int
    auto_approved: int
    needs_review: int

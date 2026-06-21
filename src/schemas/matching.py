// src/schemas/matching.py
"""Matching schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MatchRecordBase(BaseModel):
    """Base schema for match record."""
    purchase_order_id: Optional[UUID] = None
    invoice_id: Optional[UUID] = None
    delivery_note_id: Optional[UUID] = None
    match_type: str


class MatchRecordResponse(MatchRecordBase):
    """Schema for match record response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    match_score: Decimal
    line_level_score: Decimal = Decimal("0")
    amount_score: Decimal = Decimal("0")
    date_score: Decimal = Decimal("0")
    decision: str
    decided_by: Optional[UUID] = None
    decided_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class MatchDecisionCreate(BaseModel):
    """Schema for creating a match decision."""
    new_decision: str = Field(..., pattern="^(CONFIRMED|REJECTED)$")
    reason: Optional[str] = None


class MatchDecisionResponse(BaseModel):
    """Schema for match decision response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    match_record_id: UUID
    user_id: Optional[UUID] = None
    previous_decision: Optional[str] = None
    new_decision: str
    reason: Optional[str] = None
    created_at: datetime


class MatchResult(BaseModel):
    """Result of a matching operation."""
    match_type: str
    match_score: Decimal
    line_level_score: Decimal
    amount_score: Decimal
    date_score: Decimal
    matched_lines: list[dict] = Field(default_factory=list)
    discrepancies: list[str] = Field(default_factory=list)


class MatchingSummary(BaseModel):
    """Summary of matching results."""
    total_invoices: int
    total_delivery_notes: int
    total_purchase_orders: int
    auto_approved: int
    pending_review: int
    rejected: int
    match_results: list[MatchResult] = Field(default_factory=list)


class MatchListResponse(BaseModel):
    """Schema for paginated match list."""
    items: list[MatchRecordResponse]
    total: int
    page: int
    page_size: int
    pages: int


class DecisionUpdateRequest(BaseModel):
    """Request to update a match decision."""
    decision: str = Field(..., pattern="^(CONFIRMED|REJECTED)$")
    notes: Optional[str] = None

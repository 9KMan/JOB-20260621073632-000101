// src/schemas/match.py
"""Match schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.document import DocumentLineResponse


class MatchLineResponse(BaseModel):
    """Match line response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    source_line_id: str
    target_line_id: str
    matched_quantity: Decimal
    variance_quantity: Decimal
    matched_amount: Decimal
    variance_amount: Decimal
    score: Decimal
    is_confirmed: bool
    confirmation_notes: Optional[str] = None


class MatchResponse(BaseModel):
    """Match response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    source_document_id: str
    target_document_id: str
    third_document_id: Optional[str] = None
    match_type: str
    total_score: Decimal
    line_score: Decimal
    amount_score: Decimal
    date_score: Decimal
    matched_amount: Decimal
    variance_amount: Decimal
    status: str
    decision: Optional[str] = None
    variance_reason: Optional[str] = None
    tolerance_notes: Optional[str] = None
    approved_by_id: Optional[str] = None
    approved_at: Optional[datetime] = None
    approval_notes: Optional[str] = None
    lines: list[MatchLineResponse] = []
    created_at: datetime
    updated_at: datetime


class MatchCreate(BaseModel):
    """Match creation schema (for manual matching)."""
    source_document_id: str
    target_document_id: str
    third_document_id: Optional[str] = None
    notes: Optional[str] = None


class MatchConfirm(BaseModel):
    """Match confirmation schema."""
    notes: Optional[str] = None


class MatchReject(BaseModel):
    """Match rejection schema."""
    reason: str = Field(..., min_length=1)


class MatchRequest(BaseModel):
    """Match request for initiating matching."""
    source_document_id: str
    target_document_id: Optional[str] = None
    include_delivery_notes: bool = True

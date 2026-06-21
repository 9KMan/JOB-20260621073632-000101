// src/schemas/match.py
"""Match schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.models.match import MatchType, MatchStatus, MatchResult
from src.schemas.common import BaseSchema, TimestampSchema


class MatchRecordBase(BaseSchema):
    """Base match record schema."""
    match_type: MatchType


class MatchRecordCreate(MatchRecordBase):
    """Match record creation schema."""
    invoice_id: Optional[UUID] = None
    purchase_order_id: Optional[UUID] = None
    delivery_note_id: Optional[UUID] = None


class MatchRecordResponse(MatchRecordBase, TimestampSchema):
    """Match record response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    invoice_id: Optional[UUID] = None
    purchase_order_id: Optional[UUID] = None
    delivery_note_id: Optional[UUID] = None
    
    quantity_match_score: Decimal
    amount_match_score: Decimal
    date_match_score: Decimal
    total_score: Decimal
    
    match_result: MatchResult
    status: MatchStatus
    
    variance_amount: Decimal
    variance_quantity: Decimal


class MatchConfirmationCreate(BaseSchema):
    """Match confirmation creation schema."""
    match_record_id: UUID
    decision: MatchStatus
    notes: Optional[str] = None


class MatchConfirmationResponse(TimestampSchema):
    """Match confirmation response schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    match_record_id: UUID
    user_id: Optional[UUID] = None
    decision: MatchStatus
    notes: Optional[str] = None


class MatchSummary(BaseSchema):
    """Match summary for a document."""
    total_matches: int
    exact_matches: int
    partial_matches: int
    pending_review: int
    auto_confirmed: int
    disputed: int

// src/api/schemas/matching.py
"""Matching API schemas."""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from enum import Enum

from pydantic import BaseModel, Field

from app.api.schemas.common import BaseSchema


class MatchTypeEnum(str, Enum):
    """Match type enum for API."""

    PO_INVOICE = "PO_INVOICE"
    PO_DELIVERY_NOTE = "PO_DELIVERY_NOTE"
    INVOICE_DELIVERY_NOTE = "INVOICE_DELIVERY_NOTE"
    THREE_WAY = "THREE_WAY"


class MatchStatusEnum(str, Enum):
    """Match status enum for API."""

    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    AUTO_APPROVED = "AUTO_APPROVED"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    REJECTED = "REJECTED"
    DISPUTED = "DISPUTED"


class MatchRequest(BaseSchema):
    """Match request schema for initiating matching."""

    invoice_id: Optional[str] = None
    delivery_note_id: Optional[str] = None
    po_id: Optional[str] = None
    match_type: Optional[MatchTypeEnum] = None  # If None, auto-detect


class MatchScoreResponse(BaseSchema):
    """Match score response schema."""

    id: str
    po_line_id: Optional[str] = None
    invoice_line_id: Optional[str] = None
    delivery_note_line_id: Optional[str] = None
    product_code_match: bool
    po_quantity: Optional[Decimal] = None
    matched_quantity: Optional[Decimal] = None
    quantity_match_score: Decimal
    po_amount: Optional[Decimal] = None
    matched_amount: Optional[Decimal] = None
    amount_match_score: Decimal
    line_score: Decimal
    is_matched: bool
    variance_reason: Optional[str] = None


class MatchResultResponse(BaseSchema):
    """Match result response schema."""

    id: str
    invoice_id: Optional[str] = None
    delivery_note_id: Optional[str] = None
    po_id: Optional[str] = None
    match_type: MatchTypeEnum
    status: MatchStatusEnum
    total_score: Decimal
    line_score: Decimal
    amount_score: Decimal
    date_score: Decimal
    po_amount: Optional[Decimal] = None
    invoice_amount: Optional[Decimal] = None
    delivery_note_amount: Optional[Decimal] = None
    amount_variance: Optional[Decimal] = None
    po_quantity: Optional[Decimal] = None
    invoice_quantity: Optional[Decimal] = None
    delivery_note_quantity: Optional[Decimal] = None
    quantity_variance: Optional[Decimal] = None
    decision: str
    decision_reason: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class MatchResultDetailResponse(MatchResultResponse):
    """Match result with detailed scores."""

    scores: list[MatchScoreResponse] = []


class DecisionResponse(BaseSchema):
    """Decision response schema."""

    decision: str
    reason: str
    action_required: Optional[str] = None
    auto_approve: bool = False


class MatchingSummaryResponse(BaseSchema):
    """Summary of matching results."""

    total_matches: int
    auto_approved: int
    pending_review: int
    rejected: int
    disputed: int
    average_score: Decimal
    total_amount_involved: Decimal
    results: list[MatchResultResponse]


class ManualReviewRequest(BaseSchema):
    """Request for manual review."""

    match_result_id: str
    decision: str = Field(..., pattern="^(CONFIRMED|REJECTED)$")
    notes: Optional[str] = None
    reviewed_by: str = Field(..., max_length=255)


class BalanceLedgerResponse(BaseSchema):
    """Balance ledger response schema."""

    id: str
    po_id: str
    invoice_id: Optional[str] = None
    delivery_note_id: Optional[str] = None
    balance_type: str
    original_amount: Decimal
    original_quantity: Decimal
    remaining_amount: Decimal
    remaining_quantity: Decimal
    billed_amount: Decimal
    billed_quantity: Decimal
    is_settled: bool
    settlement_date: Optional[date] = None
    effective_date: date

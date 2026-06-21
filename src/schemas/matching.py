// src/schemas/matching.py
"""Matching schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from src.schemas.common import BaseSchema, TimestampMixin


class MatchingLineDetail(BaseSchema):
    """Detail of a line-level match."""
    po_line_id: Optional[UUID] = None
    invoice_line_id: Optional[UUID] = None
    delivery_line_id: Optional[UUID] = None
    item_code: str
    po_quantity: Decimal
    invoice_quantity: Decimal
    delivery_quantity: Decimal
    matched_quantity: Decimal
    quantity_variance: Decimal
    quantity_score: Decimal


class VarianceDetail(BaseSchema):
    """Variance details."""
    amount_variance: Decimal
    quantity_variance: Decimal
    price_variance: Decimal
    date_variance_days: int
    variance_reason: Optional[str] = None


class MatchingRecordBase(BaseSchema):
    """Base matching record schema."""
    match_type: str
    status: str


class MatchingRecordCreate(BaseSchema):
    """Schema for creating a matching record."""
    match_type: str
    purchase_order_id: Optional[UUID] = None
    invoice_id: Optional[UUID] = None
    delivery_note_id: Optional[UUID] = None


class MatchingRecordResponse(MatchingRecordBase, TimestampMixin):
    """Schema for matching record response."""
    id: UUID
    decision: Optional[str] = None
    overall_score: Decimal
    line_level_score: Decimal
    amount_score: Decimal
    date_score: Decimal
    confidence_level: str
    purchase_order_id: Optional[UUID] = None
    invoice_id: Optional[UUID] = None
    delivery_note_id: Optional[UUID] = None
    po_amount: Decimal
    invoice_amount: Decimal
    delivery_amount: Decimal
    matched_amount: Decimal
    variance_amount: Decimal
    quantity_variance: Decimal
    amount_variance: Decimal
    price_variance: Decimal
    date_variance_days: int
    line_match_details: Optional[dict[str, Any]] = None
    variance_details: Optional[dict[str, Any]] = None
    review_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    confirmed_by_id: Optional[UUID] = None
    confirmed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class MatchDecisionRequest(BaseSchema):
    """Request schema for making a matching decision."""
    decision: str = Field(..., description="auto_approved, human_review, or rejected")
    review_notes: Optional[str] = None
    rejection_reason: Optional[str] = None


class MatchConfirmationFeedback(BaseSchema):
    """Feedback data for the learning loop."""
    correct_match: bool
    suggested_corrections: Optional[dict[str, Any]] = None
    notes: Optional[str] = None


class MatchingSummary(BaseSchema):
    """Summary of matching results."""
    total_records: int
    auto_approved: int
    pending_review: int
    rejected: int
    unmatched: int
    average_score: float


class MatchableDocument(BaseSchema):
    """Schema for documents eligible for matching."""
    id: UUID
    document_number: str
    document_type: str
    supplier_id: str
    supplier_name: str
    amount: Decimal
    date: str
    status: str
    line_count: int


class MatchCandidatesRequest(BaseSchema):
    """Request to find match candidates for a document."""
    document_type: str
    document_id: UUID
    match_type: Optional[str] = None

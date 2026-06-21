// src/schemas/match.py
"""Match-related Pydantic schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.base import BaseSchema, TimestampMixin
from src.schemas.purchase_order import PurchaseOrderSummary
from src.schemas.invoice import InvoiceSummary
from src.schemas.delivery_note import DeliveryNoteSummary


class MatchLineResponse(BaseSchema):
    """Schema for match line response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    match_id: UUID
    line_number: int
    sku_matched: bool
    sku_source: Optional[str] = None
    sku_target: Optional[str] = None
    quantity_source: Decimal
    quantity_target: Decimal
    quantity_variance: Decimal
    quantity_match_score: Decimal
    price_source: Decimal
    price_target: Decimal
    price_variance: Decimal
    price_match_score: Decimal
    amount_source: Decimal
    amount_target: Decimal
    amount_variance: Decimal
    amount_match_score: Decimal
    is_matched: bool
    match_confidence: Decimal


class MatchBase(BaseSchema):
    """Base match schema."""

    match_type: str
    status: str = "pending"


class MatchCreate(MatchBase):
    """Schema for creating a match."""

    purchase_order_id: Optional[UUID] = None
    invoice_id: Optional[UUID] = None
    delivery_note_id: Optional[UUID] = None


class MatchUpdate(BaseSchema):
    """Schema for updating a match."""

    status: Optional[str] = None
    decision: Optional[str] = None
    decision_notes: Optional[str] = None
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None


class MatchResponse(MatchBase, TimestampMixin):
    """Schema for match response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    purchase_order_id: Optional[UUID] = None
    invoice_id: Optional[UUID] = None
    delivery_note_id: Optional[UUID] = None

    # Scores
    line_level_score: Decimal
    amount_score: Decimal
    date_score: Decimal
    overall_score: Decimal

    # Amounts
    po_amount: Decimal
    invoice_amount: Decimal
    delivery_note_amount: Decimal
    variance_amount: Decimal

    # Variance
    quantity_variance: Decimal
    price_variance: Decimal

    # Decision
    decision: Optional[str] = None
    decision_notes: Optional[str] = None
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None

    # Nested documents
    purchase_order: Optional[PurchaseOrderSummary] = None
    invoice: Optional[InvoiceSummary] = None
    delivery_note: Optional[DeliveryNoteSummary] = None
    lines: list[MatchLineResponse] = Field(default_factory=list)


class MatchDecision(BaseSchema):
    """Schema for match decision."""

    match_id: UUID
    decision: str = Field(
        description="Decision: AUTO_APPROVE, HUMAN_REVIEW, or DISPUTE"
    )
    notes: Optional[str] = Field(default=None, max_length=1000)
    reviewed_by: UUID


class MatchingResult(BaseSchema):
    """Schema for matching result summary."""

    total_matches: int
    auto_approved: int
    pending_review: int
    rejected: int
    average_score: Decimal
    matches: list[MatchResponse]


class MatchScoreDetail(BaseSchema):
    """Detailed score breakdown for matching."""

    line_level_score: Decimal
    amount_score: Decimal
    date_score: Decimal
    overall_score: Decimal
    breakdown: dict[str, Decimal] = Field(default_factory=dict)


class MatchCandidate(BaseSchema):
    """Schema for potential match candidate."""

    document_id: UUID
    document_type: str
    document_number: str
    match_score: Decimal
    match_type: str
    matched_lines: int
    total_lines: int

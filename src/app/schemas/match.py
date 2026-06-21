// src/app/schemas/match.py
"""
Match schemas for API request/response validation.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.base import BaseSchema, TimestampSchema, PaginationParams, PaginatedResponse
from app.schemas.invoice import InvoiceBrief
from app.schemas.delivery_note import DeliveryNoteBrief
from app.schemas.purchase_order import PurchaseOrderBrief


class MatchLineScore(BaseSchema):
    """Individual line match score."""
    invoice_line_id: UUID
    po_line_id: Optional[UUID]
    dn_line_id: Optional[UUID]
    quantity_match_score: Decimal
    description_match_score: Decimal
    sku_match_score: Decimal
    line_score: Decimal


class MatchCreate(BaseSchema):
    """Schema for creating a match (manual trigger)."""
    invoice_id: UUID
    delivery_note_id: Optional[UUID] = None
    purchase_order_id: Optional[UUID] = None


class MatchResponse(TimestampSchema):
    """Match response schema."""
    id: UUID
    invoice_id: UUID
    delivery_note_id: Optional[UUID]
    purchase_order_id: Optional[UUID]
    match_type: str
    status: str
    line_level_score: Decimal
    amount_score: Decimal
    date_score: Decimal
    total_score: Decimal
    quantity_variance: Decimal
    amount_variance: Decimal
    decision: str
    decision_notes: Optional[str]
    decided_by: Optional[UUID]
    decided_at: Optional[datetime]
    invoice: Optional[InvoiceBrief] = None
    delivery_note: Optional[DeliveryNoteBrief] = None
    purchase_order: Optional[PurchaseOrderBrief] = None


class MatchListResponse(PaginatedResponse[MatchResponse]):
    """Paginated match list response."""
    pass


class MatchDecision(BaseSchema):
    """Schema for match decision."""
    match_id: UUID
    decision: str = Field(..., description="Decision: confirmed, rejected, adjusted")
    comments: Optional[str] = None
    adjusted_quantity: Optional[Decimal] = None
    adjusted_amount: Optional[Decimal] = None


class MatchSummary(BaseSchema):
    """Summary of match results."""
    total_matches: int
    auto_approved: int
    pending_review: int
    rejected: int
    average_score: Decimal


class MatchStatistics(BaseSchema):
    """Overall matching statistics."""
    summary: MatchSummary
    matches_by_type: dict
    recent_matches: List[MatchResponse]

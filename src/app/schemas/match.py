// src/app/schemas/match.py
"""
Match Result schemas.
"""
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field

from app.schemas.common import BaseSchema, TimestampMixin, SearchParams


class MatchResultBase(BaseModel):
    """Base match result schema."""
    invoice_id: str
    po_id: Optional[str] = None
    dn_id: Optional[str] = None


class MatchResultCreate(MatchResultBase):
    """Match result creation schema."""
    line_match_score: Optional[Decimal] = None
    amount_match_score: Optional[Decimal] = None
    date_match_score: Optional[Decimal] = None
    overall_match_score: Optional[Decimal] = None
    decision: Optional[str] = "PENDING_REVIEW"
    variance_amount: Optional[Decimal] = None
    variance_quantity: Optional[Decimal] = None
    variance_reason: Optional[str] = None


class MatchResultUpdate(BaseModel):
    """Match result update schema."""
    decision: Optional[str] = None
    confirmation_notes: Optional[str] = None
    variance_reason: Optional[str] = None
    status: Optional[str] = None


class MatchResultResponse(MatchResultBase, TimestampMixin):
    """Match result response schema."""
    id: str
    line_match_score: Decimal
    amount_match_score: Decimal
    date_match_score: Decimal
    overall_match_score: Decimal
    decision: str
    invoice_amount: Decimal
    po_amount: Optional[Decimal] = None
    dn_amount: Optional[Decimal] = None
    variance_amount: Decimal
    invoice_quantity: Decimal
    po_quantity: Optional[Decimal] = None
    dn_quantity: Optional[Decimal] = None
    variance_quantity: Decimal
    price_variance: Optional[Decimal] = None
    quantity_variance: Optional[Decimal] = None
    variance_reason: Optional[str] = None
    confirmed_by_id: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    confirmation_notes: Optional[str] = None
    status: str
    layer: int
    is_confirmed: bool = False
    is_variance: bool = False


class MatchConfirmationRequest(BaseModel):
    """Match confirmation request schema."""
    confirmed: bool
    confirmation_notes: Optional[str] = Field(default=None, max_length=1000)
    decision: Optional[str] = Field(default=None, pattern="^(AUTO_APPROVED|PENDING_REVIEW|DISPUTED)$")


class MatchSearchParams(SearchParams):
    """Match search parameters."""
    invoice_id: Optional[str] = None
    po_id: Optional[str] = None
    dn_id: Optional[str] = None
    decision: Optional[str] = None
    status: Optional[str] = None
    min_score: Optional[float] = Field(default=None, ge=0, le=1)
    max_score: Optional[float] = Field(default=None, ge=0, le=1)
    date_from: Optional[date] = None
    date_to: Optional[date] = None


class MatchBatchRequest(BaseModel):
    """Batch match request schema."""
    invoice_ids: List[str] = Field(..., min_length=1)
    po_id: Optional[str] = None
    dn_id: Optional[str] = None


class MatchBatchResponse(BaseModel):
    """Batch match response schema."""
    processed: int
    matched: int
    pending: int
    failed: int
    results: List[MatchResultResponse]

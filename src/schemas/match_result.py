// src/schemas/match_result.py
"""Match Result schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.base import BaseSchema


class MatchResultLineBase(BaseSchema):
    """Base match result line schema."""
    po_line_id: Optional[str] = None
    invoice_line_id: Optional[str] = None
    dn_line_id: Optional[str] = None
    match_score: Decimal = Decimal("0.0000")
    po_quantity: Optional[Decimal] = None
    invoice_quantity: Optional[Decimal] = None
    dn_quantity: Optional[Decimal] = None
    matched_quantity: Decimal = Decimal("0")
    variance_quantity: Decimal = Decimal("0")
    po_amount: Optional[Decimal] = None
    invoice_amount: Optional[Decimal] = None
    dn_amount: Optional[Decimal] = None
    matched_amount: Decimal = Decimal("0.00")
    variance_amount: Decimal = Decimal("0.00")
    po_unit_price: Optional[Decimal] = None
    invoice_unit_price: Optional[Decimal] = None
    dn_unit_price: Optional[Decimal] = None
    price_variance: Decimal = Decimal("0")
    price_variance_percent: Decimal = Decimal("0.0000")
    item_code: Optional[str] = None
    item_description: Optional[str] = None
    match_status: str = "matched"


class MatchResultLineCreate(MatchResultLineBase):
    """Match result line creation schema."""
    pass


class MatchResultLineResponse(MatchResultLineBase):
    """Match result line response schema."""
    id: str
    match_result_id: str
    created_at: datetime
    updated_at: datetime


class MatchResultBase(BaseSchema):
    """Base match result schema."""
    po_id: Optional[str] = None
    invoice_id: Optional[str] = None
    dn_id: Optional[str] = None
    overall_score: Decimal = Decimal("0.0000")
    po_invoice_score: Optional[Decimal] = None
    po_dn_score: Optional[Decimal] = None
    invoice_dn_score: Optional[Decimal] = None
    po_amount: Optional[Decimal] = None
    invoice_amount: Optional[Decimal] = None
    dn_amount: Optional[Decimal] = None
    amount_variance: Decimal = Decimal("0.00")
    amount_variance_percent: Decimal = Decimal("0.0000")
    total_quantity_po: Optional[Decimal] = None
    total_quantity_invoice: Optional[Decimal] = None
    total_quantity_dn: Optional[Decimal] = None
    quantity_variance: Decimal = Decimal("0")
    match_status: str = "pending"
    decision: str
    match_type: str = "full"
    auto_approved_amount: Decimal = Decimal("0.00")
    pending_review_amount: Decimal = Decimal("0.00")
    disputed_amount: Decimal = Decimal("0.00")
    resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    layer: int = 1
    match_sequence: int = 1
    po_date: Optional[date] = None
    invoice_date: Optional[date] = None
    dn_date: Optional[date] = None
    has_amount_variance: bool = False
    has_quantity_variance: bool = False
    has_date_variance: bool = False
    has_price_variance: bool = False


class MatchResultCreate(MatchResultBase):
    """Match result creation schema."""
    lines: List[MatchResultLineCreate] = Field(default_factory=list)


class MatchResultUpdate(BaseSchema):
    """Match result update schema."""
    match_status: Optional[str] = None
    decision: Optional[str] = None
    resolved: Optional[bool] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    auto_approved_amount: Optional[Decimal] = None
    pending_review_amount: Optional[Decimal] = None
    disputed_amount: Optional[Decimal] = None
    confirmed_by: Optional[str] = None
    confirmed_at: Optional[datetime] = None


class MatchResultResponse(MatchResultBase):
    """Match result response schema."""
    id: str
    matched_by: Optional[str] = None
    confirmed_by: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    lines: List[MatchResultLineResponse] = Field(default_factory=list)
    is_auto_approvable: bool = Field(default=False, exclude=True)
    needs_human_review: bool = Field(default=False, exclude=True)


class MatchRequest(BaseSchema):
    """Request to match documents."""
    invoice_id: str
    dn_id: Optional[str] = None
    po_id: Optional[str] = None
    force_match: bool = False


class MatchResponse(BaseSchema):
    """Response from matching operation."""
    success: bool
    match_result: Optional[MatchResultResponse] = None
    message: str
    auto_approved: bool = False
    requires_review: bool = False


class MatchDecision(BaseSchema):
    """Decision on a match result."""
    match_result_id: str
    decision: str  # approve, reject, dispute
    notes: Optional[str] = None
    amount_override: Optional[Decimal] = None

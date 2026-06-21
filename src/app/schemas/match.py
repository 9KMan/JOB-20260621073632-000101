// src/app/schemas/match.py
"""Match schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import BaseSchema, TimestampMixin, UUIDMixin


class MatchLineBase(BaseModel):
    """Match Line base schema."""

    match_type: str
    score: Decimal = Field(ge=0, le=100)
    quantity_match: bool = False
    price_match: bool = False
    product_match: bool = False
    invoice_quantity: Optional[Decimal] = None
    dn_quantity: Optional[Decimal] = None
    po_quantity: Optional[Decimal] = None
    matched_quantity: Decimal = Field(default=Decimal("0.00"))
    invoice_amount: Optional[Decimal] = None
    po_amount: Optional[Decimal] = None
    variance_quantity: Decimal = Field(default=Decimal("0.00"))
    variance_amount: Decimal = Field(default=Decimal("0.00"))


class MatchLineCreate(MatchLineBase):
    """Match Line creation schema."""

    invoice_line_id: Optional[UUID] = None
    dn_line_id: Optional[UUID] = None
    po_line_id: Optional[UUID] = None


class MatchLineResponse(MatchLineBase, UUIDMixin, TimestampMixin):
    """Match Line response schema."""

    model_config = ConfigDict(from_attributes=True)

    invoice_line_id: Optional[str] = None
    dn_line_id: Optional[str] = None
    po_line_id: Optional[str] = None


class MatchBase(BaseModel):
    """Match base schema."""

    invoice_id: Optional[UUID] = None
    dn_id: Optional[UUID] = None
    po_id: Optional[UUID] = None
    match_type: str
    status: str = "pending"
    result: str = "no_match"
    overall_score: Decimal = Field(default=Decimal("0.00"))
    line_level_score: Decimal = Field(default=Decimal("0.00"))
    amount_score: Decimal = Field(default=Decimal("0.00"))
    date_score: Decimal = Field(default=Decimal("0.00"))
    invoice_amount: Optional[Decimal] = None
    dn_amount: Optional[Decimal] = None
    po_amount: Optional[Decimal] = None
    variance_amount: Decimal = Field(default=Decimal("0.00"))
    match_date: date
    notes: Optional[str] = None


class MatchCreate(MatchBase):
    """Match creation schema."""

    lines: list[MatchLineCreate] = Field(default_factory=list)


class MatchUpdate(BaseModel):
    """Match update schema."""

    status: Optional[str] = None
    result: Optional[str] = None
    decision_notes: Optional[str] = None
    notes: Optional[str] = None


class MatchResponse(MatchBase, UUIDMixin, TimestampMixin):
    """Match response schema."""

    model_config = ConfigDict(from_attributes=True)

    decision_date: Optional[date] = None
    decision_notes: Optional[str] = None
    scoring_details: Optional[dict[str, Any]] = None
    lines: list[MatchLineResponse] = Field(default_factory=list)


class MatchListResponse(BaseModel):
    """Match list response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    invoice_id: Optional[str] = None
    dn_id: Optional[str] = None
    po_id: Optional[str] = None
    match_type: str
    status: str
    result: str
    overall_score: Decimal
    match_date: date
    created_at: datetime


class MatchDecisionRequest(BaseModel):
    """Request schema for match decision."""

    match_id: UUID
    decision: str = Field(pattern="^(confirmed|rejected)$")
    notes: Optional[str] = None


class MatchScoreBreakdown(BaseModel):
    """Match score breakdown."""

    line_level_score: Decimal
    amount_score: Decimal
    date_score: Decimal
    overall_score: Decimal
    details: dict[str, Any] = Field(default_factory=dict)

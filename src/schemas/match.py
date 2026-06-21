# src/schemas/match.py
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from src.schemas.common import TimestampMixinSchema, UUIDMixinSchema


class MatchBase(BaseModel):
    """Base schema for Matches."""
    match_type: str
    status: str = "PENDING"
    confidence_score: Decimal = Field(ge=0, le=1)
    line_score: Decimal = Field(ge=0, le=1)
    amount_score: Decimal = Field(ge=0, le=1)
    date_score: Decimal = Field(ge=0, le=1)


class MatchCreate(MatchBase):
    """Schema for creating Matches."""
    purchase_order_id: Optional[str] = None
    invoice_id: Optional[str] = None
    delivery_note_id: Optional[str] = None
    po_amount: Optional[Decimal] = None
    invoice_amount: Optional[Decimal] = None
    delivery_amount: Optional[Decimal] = None
    variance_amount: Optional[Decimal] = None


class MatchUpdate(BaseModel):
    """Schema for updating Matches."""
    status: Optional[str] = None
    decision: Optional[str] = None
    review_notes: Optional[str] = None


class MatchReviewRequest(BaseModel):
    """Schema for reviewing a Match."""
    status: str = Field(description="CONFIRMED or REJECTED")
    review_notes: Optional[str] = None


class MatchResponse(MatchBase, UUIDMixinSchema, TimestampMixinSchema):
    """Schema for Match response."""
    purchase_order_id: Optional[str]
    invoice_id: Optional[str]
    delivery_note_id: Optional[str]
    po_amount: Optional[Decimal]
    invoice_amount: Optional[Decimal]
    delivery_amount: Optional[Decimal]
    variance_amount: Optional[Decimal]
    reviewed_by: Optional[str]
    reviewed_at: Optional[datetime]
    review_notes: Optional[str]
    decision: Optional[str]
    auto_approved: bool
    
    model_config = {"from_attributes": True}

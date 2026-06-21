// src/app/schemas/match.py
"""Match schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MatchLineDetailBase(BaseModel):
    """Base match line detail schema."""

    invoice_line_id: Optional[UUID] = None
    po_line_id: Optional[UUID] = None
    dn_line_id: Optional[UUID] = None
    line_match_type: str = Field(default="SKU_MATCH", max_length=50)
    quantity_match: Decimal = Field(default=Decimal("0"))
    quantity_variance: Decimal = Field(default=Decimal("0"))
    amount_match: Decimal = Field(default=Decimal("0"))
    amount_variance: Decimal = Field(default=Decimal("0"))
    match_score: Decimal = Field(default=Decimal("0"))
    notes: Optional[str] = None


class MatchLineDetailResponse(MatchLineDetailBase):
    """Match line detail response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    match_id: UUID
    created_at: datetime
    updated_at: datetime


class MatchConfirmationBase(BaseModel):
    """Base match confirmation schema."""

    original_decision: str = Field(..., max_length=50)
    confirmed_decision: str = Field(..., max_length=50)
    original_score: Decimal
    override_reason: str
    is_approval: bool = True


class MatchConfirmationCreate(MatchConfirmationBase):
    """Schema for creating a match confirmation."""

    pass


class MatchConfirmationResponse(MatchConfirmationBase):
    """Match confirmation response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    match_id: UUID
    confirmed_by_id: UUID
    created_at: datetime
    updated_at: datetime
    confirmed_by_email: Optional[str] = None
    confirmed_by_name: Optional[str] = None


class MatchBase(BaseModel):
    """Base match schema."""

    invoice_id: UUID
    delivery_note_id: Optional[UUID] = None
    purchase_order_id: UUID
    match_type: str = Field(..., max_length=50)
    status: str = Field(default="PENDING", max_length=50)
    decision: Optional[str] = Field(None, max_length=50)
    line_score: Decimal = Field(default=Decimal("0"))
    amount_score: Decimal = Field(default=Decimal("0"))
    date_score: Decimal = Field(default=Decimal("0"))
    total_score: Decimal = Field(default=Decimal("0"))
    po_amount: Decimal = Field(default=Decimal("0.00"))
    invoice_amount: Decimal = Field(default=Decimal("0.00"))
    dn_amount: Decimal = Field(default=Decimal("0.00"))
    variance_amount: Decimal = Field(default=Decimal("0.00"))
    notes: Optional[str] = None


class MatchCreate(MatchBase):
    """Schema for creating a match."""

    line_details: list[MatchLineDetailBase] = []


class MatchUpdate(BaseModel):
    """Schema for updating a match."""

    status: Optional[str] = Field(None, max_length=50)
    decision: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class MatchResolve(BaseModel):
    """Schema for resolving a match."""

    decision: str = Field(..., max_length=50)
    notes: Optional[str] = None


class MatchResponse(MatchBase):
    """Match response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    resolved_at: Optional[datetime] = None
    resolved_by_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime


class MatchDetailResponse(MatchResponse):
    """Match detail response with line details."""

    line_details: list[MatchLineDetailResponse] = []
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    dn_number: Optional[str] = None
    delivery_date: Optional[date] = None
    po_number: Optional[str] = None
    order_date: Optional[date] = None
    supplier_name: Optional[str] = None
    confirmations: list[MatchConfirmationResponse] = []


class MatchListResponse(BaseModel):
    """Schema for match list response."""

    items: list[MatchDetailResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class MatchScoreSummary(BaseModel):
    """Summary of match scores for dashboard."""

    total_matches: int
    auto_approved: int
    pending_review: int
    in_dispute: int
    average_score: Decimal
    average_line_score: Decimal
    average_amount_score: Decimal
    average_date_score: Decimal
    total_variance: Decimal

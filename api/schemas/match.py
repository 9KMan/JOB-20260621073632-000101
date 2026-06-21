# api/schemas/match.py
"""Match schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, Field


class MatchLineBase(BaseModel):
    """Match Line base schema."""

    item_match_score: Decimal = Field(default=Decimal("0.0000"))
    quantity_match_score: Decimal = Field(default=Decimal("0.0000"))
    price_match_score: Decimal = Field(default=Decimal("0.0000"))
    line_total_score: Decimal = Field(default=Decimal("0.0000"))
    quantity_variance: Decimal = Field(default=Decimal("0.0000"))
    price_variance: Decimal = Field(default=Decimal("0.0000"))
    amount_variance: Decimal = Field(default=Decimal("0.00"))
    variance_reason: Optional[str] = None
    notes: Optional[str] = None


class MatchLineResponse(MatchLineBase):
    """Match Line response schema."""

    id: str
    match_id: str
    invoice_line_id: Optional[str] = None
    po_line_id: Optional[str] = None
    dn_line_id: Optional[str] = None
    invoice_quantity: Optional[Decimal] = None
    po_quantity: Optional[Decimal] = None
    dn_quantity: Optional[Decimal] = None
    invoice_unit_price: Optional[Decimal] = None
    po_unit_price: Optional[Decimal] = None
    dn_unit_price: Optional[Decimal] = None
    invoice_line_amount: Optional[Decimal] = None
    po_line_amount: Optional[Decimal] = None
    dn_line_amount: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MatchBase(BaseModel):
    """Match base schema."""

    match_type: str = Field(min_length=1, max_length=20)
    line_level_score: Decimal = Field(default=Decimal("0.0000"))
    amount_score: Decimal = Field(default=Decimal("0.0000"))
    date_score: Decimal = Field(default=Decimal("0.0000"))
    total_score: Decimal = Field(default=Decimal("0.0000"))
    status: str = Field(default="PENDING", max_length=20)
    variance_amount: Decimal = Field(default=Decimal("0.00"))
    variance_percentage: Decimal = Field(default=Decimal("0.0000"))
    variance_reason: Optional[str] = None
    notes: Optional[str] = None


class MatchCreate(MatchBase):
    """Match creation schema."""

    invoice_id: Optional[str] = None
    delivery_note_id: Optional[str] = None
    purchase_order_id: Optional[str] = None


class MatchResponse(MatchBase):
    """Match response schema."""

    id: str
    invoice_id: Optional[str] = None
    delivery_note_id: Optional[str] = None
    purchase_order_id: Optional[str] = None
    invoice_amount: Optional[Decimal] = None
    po_amount: Optional[Decimal] = None
    dn_amount: Optional[Decimal] = None
    confirmed_by: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    lines: list[MatchLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MatchListResponse(BaseModel):
    """Match list response schema."""

    id: str
    match_type: str
    invoice_number: Optional[str] = None
    po_number: Optional[str] = None
    dn_number: Optional[str] = None
    total_score: Decimal
    status: str
    variance_amount: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


class MatchConfirmRequest(BaseModel):
    """Match confirmation request."""

    notes: Optional[str] = None


class MatchRejectRequest(BaseModel):
    """Match rejection request."""

    reason: str = Field(min_length=1, max_length=500)
    notes: Optional[str] = None


class MatchStatusUpdate(BaseModel):
    """Match status update request."""

    status: str = Field(min_length=1, max_length=20)
    notes: Optional[str] = None


class MatchGenerateRequest(BaseModel):
    """Request to generate matches for a document."""

    document_type: str = Field(min_length=1, max_length=20)
    document_id: str = Field(min_length=1)
    match_types: Optional[list[str]] = None


class MatchScoreResponse(BaseModel):
    """Match score breakdown response."""

    line_level_score: Decimal
    amount_score: Decimal
    date_score: Decimal
    total_score: Decimal
    weighted_line_level: Decimal
    weighted_amount: Decimal
    weighted_date: Decimal

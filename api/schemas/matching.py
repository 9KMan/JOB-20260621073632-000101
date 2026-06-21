// api/schemas/matching.py
"""Matching schemas for 3-way matching engine."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field


class MatchLineDetailResponse(BaseModel):
    """Schema for match line detail response."""
    id: UUID
    item_code: str
    po_quantity: Optional[Decimal] = None
    po_unit_price: Optional[Decimal] = None
    document_quantity: Optional[Decimal] = None
    document_unit_price: Optional[Decimal] = None
    quantity_match: Optional[bool] = None
    price_match: Optional[bool] = None
    line_score: Optional[Decimal] = None
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


class MatchResponse(BaseModel):
    """Schema for match response."""
    id: UUID
    match_type: str
    invoice_id: Optional[UUID] = None
    dn_id: Optional[UUID] = None
    po_id: Optional[UUID] = None
    line_score: Decimal
    amount_score: Decimal
    date_score: Decimal
    total_score: Decimal
    po_amount: Optional[Decimal] = None
    document_amount: Optional[Decimal] = None
    variance_amount: Optional[Decimal] = None
    variance_percentage: Optional[Decimal] = None
    status: str
    decision: Optional[str] = None
    match_details: Optional[dict] = None
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[str] = None
    review_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    line_details: List[MatchLineDetailResponse] = []

    model_config = {"from_attributes": True}


class MatchCreate(BaseModel):
    """Schema for creating a match record (manual matching)."""
    match_type: str
    invoice_id: Optional[UUID] = None
    dn_id: Optional[UUID] = None
    po_id: Optional[UUID] = None


class MatchReview(BaseModel):
    """Schema for reviewing a match."""
    status: str = Field(..., description="confirmed or rejected")
    notes: Optional[str] = None


class MatchResult(BaseModel):
    """Schema for a single matching result."""
    match_id: UUID
    match_type: str
    score: Decimal
    decision: str
    invoice_id: Optional[UUID] = None
    invoice_number: Optional[str] = None
    dn_id: Optional[UUID] = None
    dn_number: Optional[str] = None
    po_id: UUID
    po_number: str
    variance_amount: Optional[Decimal] = None
    variance_percentage: Optional[Decimal] = None
    line_details: List[dict] = []


class MatchingResult(BaseModel):
    """Schema for the complete matching result."""
    invoice_id: Optional[UUID] = None
    invoice_number: Optional[str] = None
    invoice_amount: Optional[Decimal] = None
    matches: List[MatchResult] = []
    best_match: Optional[MatchResult] = None
    total_matches: int = 0
    message: str


class MatchingRequest(BaseModel):
    """Schema for requesting matching."""
    invoice_id: Optional[UUID] = None
    dn_id: Optional[UUID] = None
    supplier_id: Optional[str] = None


class BalanceResponse(BaseModel):
    """Schema for balance response."""
    id: UUID
    document_type: str
    document_id: UUID
    document_number: str
    balance_type: str
    original_amount: Decimal
    original_quantity: Decimal
    matched_amount: Decimal
    matched_quantity: Decimal
    remaining_amount: Decimal
    remaining_quantity: Decimal
    is_settled: bool
    settlement_date: Optional[str] = None
    notes: Optional[str] = None
    po_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

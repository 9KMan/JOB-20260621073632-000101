// src/schemas/match.py
"""Match schemas for 3-way matching."""
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MatchLineDetail(BaseModel):
    """Line item match details."""
    source_line_number: int
    target_line_number: int
    source_item_code: str
    target_item_code: str
    quantity_match: bool
    price_match: bool
    quantity_variance: Decimal
    price_variance: Decimal
    line_score: Decimal


class MatchBase(BaseModel):
    """Base match schema."""
    invoice_id: Optional[UUID] = None
    delivery_note_id: Optional[UUID] = None
    purchase_order_id: Optional[UUID] = None


class MatchCreate(MatchBase):
    """Schema for match creation."""
    line_matches: Optional[list[MatchLineDetail]] = None


class MatchUpdate(BaseModel):
    """Schema for match update."""
    match_status: Optional[str] = None
    decision: Optional[str] = None
    review_notes: Optional[str] = None


class MatchResponse(MatchBase):
    """Schema for match response."""
    id: UUID
    line_level_score: Decimal
    amount_score: Decimal
    date_score: Decimal
    overall_score: Decimal
    match_type: str
    match_status: str
    decision: str
    invoice_amount: Optional[Decimal] = None
    po_amount: Optional[Decimal] = None
    dn_amount: Optional[Decimal] = None
    variance_amount: Decimal
    line_matches: Optional[list[dict[str, Any]]] = None
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class MatchListResponse(BaseModel):
    """Schema for paginated match list."""
    items: list[MatchResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class MatchSummary(BaseModel):
    """Summary of matching results."""
    total_matches: int
    auto_approved: int
    pending_review: int
    rejected: int
    average_score: Decimal
    total_variance: Decimal


class BalanceLedgerEntryResponse(BaseModel):
    """Schema for balance ledger entry response."""
    id: UUID
    balance_ledger_id: UUID
    match_id: Optional[UUID] = None
    entry_type: str
    amount: Decimal
    balance_after: Decimal
    reference_document_type: Optional[str] = None
    reference_document_id: Optional[UUID] = None
    reference_document_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}


class BalanceLedgerResponse(BaseModel):
    """Schema for balance ledger response."""
    id: UUID
    document_type: str
    document_id: UUID
    document_number: str
    original_amount: Decimal
    matched_amount: Decimal
    pending_amount: Decimal
    balance_status: str
    created_at: datetime
    updated_at: datetime
    entries: list[BalanceLedgerEntryResponse] = []
    
    model_config = {"from_attributes": True}

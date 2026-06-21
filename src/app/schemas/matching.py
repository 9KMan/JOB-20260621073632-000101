// src/app/schemas/matching.py
"""Matching Pydantic schemas."""

from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field

from src.app.schemas.invoice import InvoiceResponse
from src.app.schemas.delivery_note import DeliveryNoteResponse
from src.app.schemas.purchase_order import PurchaseOrderResponse


class MatchResultBase(BaseModel):
    """Base match result schema."""

    match_type: str
    match_score: Decimal
    decision: str


class MatchResultResponse(MatchResultBase):
    """Schema for match result response."""

    id: str
    invoice_id: Optional[str] = None
    delivery_note_id: Optional[str] = None
    purchase_order_id: Optional[str] = None
    line_level_score: Optional[Decimal] = None
    amount_score: Optional[Decimal] = None
    date_score: Optional[Decimal] = None
    auto_processed: str
    invoice_amount: Optional[Decimal] = None
    po_amount: Optional[Decimal] = None
    dn_amount: Optional[Decimal] = None
    variance_amount: Optional[Decimal] = None
    details: Optional[str] = None
    discrepancy_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    invoice: Optional[InvoiceResponse] = None
    delivery_note: Optional[DeliveryNoteResponse] = None
    purchase_order: Optional[PurchaseOrderResponse] = None

    class Config:
        from_attributes = True


class MatchResultListResponse(BaseModel):
    """Schema for paginated match result list response."""

    items: List[MatchResultResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class MatchDecisionUpdate(BaseModel):
    """Schema for updating match decision."""

    decision: str = Field(..., pattern="^(CONFIRMED|PENDING|REJECTED)$")
    comments: Optional[str] = None


class HumanConfirmationCreate(BaseModel):
    """Schema for creating human confirmation."""

    confirmed_by: str = Field(..., min_length=1, max_length=255)
    confirmation_date: str = Field(..., max_length=50)
    original_decision: str = Field(..., pattern="^(CONFIRMED|PENDING|REJECTED)$")
    new_decision: str = Field(..., pattern="^(CONFIRMED|PENDING|REJECTED)$")
    comments: Optional[str] = None
    confidence_boost: Optional[Decimal] = Field(None, ge=0, le=1)


class MatchRequest(BaseModel):
    """Schema for manual match request."""

    invoice_id: Optional[str] = None
    delivery_note_id: Optional[str] = None
    purchase_order_id: Optional[str] = None
    match_type: str = Field(..., pattern="^(INVOICE_PO|DELIVERY_NOTE_PO|INVOICE_DELIVERY_NOTE|THREE_WAY)$")


class MatchSummaryResponse(BaseModel):
    """Schema for matching summary response."""

    total_matches: int
    confirmed: int
    pending: int
    rejected: int
    auto_approved: int
    human_review: int

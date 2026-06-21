// src/schemas/matching.py
"""Matching schemas."""
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field

from src.schemas.common import BaseSchema, PaginatedResponse, TimestampMixin
from src.schemas.invoice import InvoiceSummary
from src.schemas.delivery_note import DeliveryNoteSummary
from src.schemas.purchase_order import PurchaseOrderSummary


class MatchRequest(BaseSchema):
    """Request for matching operations."""
    invoice_id: Optional[UUID] = None
    dn_id: Optional[UUID] = None
    po_id: Optional[UUID] = None
    match_type: Optional[str] = None  # auto-detect if not specified


class MatchResponse(BaseSchema):
    """Response for matching operations."""
    match_record: "MatchRecordResponse"
    decision: str
    balance_updates: List["BalanceLedgerResponse"] = Field(default_factory=list)


class MatchRecordBase(BaseSchema):
    """Base match record schema."""
    match_type: str
    status: str
    line_score: Decimal
    amount_score: Decimal
    date_score: Decimal
    total_score: Decimal
    matched_amount: Decimal
    variance_amount: Decimal
    quantity_variance: Optional[Decimal] = None
    amount_variance: Optional[Decimal] = None
    variance_reason: Optional[str] = None


class MatchRecordResponse(MatchRecordBase, TimestampMixin):
    """Schema for match record response."""
    id: UUID
    invoice_id: Optional[UUID] = None
    dn_id: Optional[UUID] = None
    po_id: Optional[UUID] = None
    decision: Optional[str] = None
    decision_notes: Optional[str] = None
    invoice: Optional[InvoiceSummary] = None
    delivery_note: Optional[DeliveryNoteSummary] = None
    purchase_order: Optional[PurchaseOrderSummary] = None


class MatchRecordListResponse(PaginatedResponse[MatchRecordResponse]):
    """Schema for paginated match records."""
    pass


class BalanceLedgerResponse(BaseSchema):
    """Schema for balance ledger response."""
    id: UUID
    document_type: str
    document_id: UUID
    document_number: str
    original_amount: Decimal
    matched_amount: Decimal
    pending_amount: Decimal
    balance: Decimal
    is_settled: bool
    match_record_id: Optional[UUID] = None
    created_at: datetime


class CrossReferenceCreate(BaseSchema):
    """Schema for creating cross reference."""
    match_record_id: UUID
    document_type: str
    document_id: UUID
    document_number: str
    matched_against_type: str
    matched_against_id: UUID
    matched_against_number: str
    confirmed: bool
    confirmation_notes: Optional[str] = None
    feature_vector: Optional[dict] = None


class CrossReferenceResponse(CrossReferenceCreate, TimestampMixin):
    """Schema for cross reference response."""
    id: UUID
    confirmed_by_id: Optional[UUID] = None


class MatchDecisionRequest(BaseSchema):
    """Request for match decision."""
    match_record_id: UUID
    decision: str  # auto_approve, human_review, dispute
    notes: Optional[str] = None


class MatchingStats(BaseSchema):
    """Statistics for matching engine."""
    total_match_records: int
    pending_matches: int
    auto_approved: int
    human_review_required: int
    disputed: int
    total_matched_amount: Decimal
    total_variance_amount: Decimal


# Update forward references
MatchResponse.model_rebuild()

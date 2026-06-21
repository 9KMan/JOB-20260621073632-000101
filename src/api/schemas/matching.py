// src/api/schemas/matching.py
"""Matching schemas for request/response validation."""
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from src.api.schemas.document import DocumentResponse


class LineMatchDetail(BaseModel):
    """Details of a matched line between documents."""
    source_line_id: UUID
    target_line_id: UUID
    match_score: float
    quantity_match: bool
    amount_match: bool
    item_code_match: bool


class MatchResults(BaseModel):
    """Internal model for match results."""
    overall_score: float
    line_matches: list[LineMatchDetail]
    amount_variance: Decimal
    quantity_variance: Decimal
    date_variance_days: int
    balance_status: str
    has_warnings: bool
    warnings: list[str]
    invoice_po_match: float
    dn_po_match: float
    invoice_dn_match: float


class MatchRequest(BaseModel):
    """Request to perform 3-way matching."""
    invoice_id: UUID
    delivery_note_id: Optional[UUID] = None
    purchase_order_id: UUID


class MatchDecision(BaseModel):
    """Decision result from the matching engine."""
    status: str
    action: str
    reason: str
    confidence: float
    requires_approval: bool
    approver_roles: Optional[list[str]] = None


class MatchResponse(BaseModel):
    """Response from a matching operation."""
    match_id: UUID
    invoice_id: UUID
    delivery_note_id: Optional[UUID]
    purchase_order_id: UUID
    status: str
    overall_score: float
    line_matches: list[LineMatchDetail]
    amount_variance: Decimal
    quantity_variance: Decimal
    date_variance: int
    balance_status: str
    warnings: list[str]
    decision: MatchDecision
    created_at: datetime


class MatchResultLineMatch(BaseModel):
    """Line match for stored match result."""
    id: UUID
    match_result_id: UUID
    source_document_type: str
    source_line_number: int
    target_document_type: str
    target_line_number: int
    match_score: float
    quantity_variance: Decimal
    amount_variance: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


class CrossReferenceResponse(BaseModel):
    """Cross reference for human confirmation."""
    id: UUID
    match_result_id: UUID
    source_document_id: UUID
    source_document_type: str
    source_line_number: int
    target_document_id: UUID
    target_document_type: str
    target_line_number: int
    match_type: str
    confirmed: Optional[bool]
    confirmed_by: Optional[str]
    confirmed_at: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MatchResultResponse(BaseModel):
    """Full match result with all details."""
    id: UUID
    invoice_id: UUID
    delivery_note_id: Optional[UUID]
    purchase_order_id: UUID
    status: str
    overall_score: float
    amount_variance: Decimal
    quantity_variance: Decimal
    date_variance_days: int
    balance_status: str
    warnings: list[str]
    line_matches: list[MatchResultLineMatch]
    cross_references: list[CrossReferenceResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BatchMatchItem(BaseModel):
    """Single match request in a batch."""
    invoice_id: UUID
    delivery_note_id: Optional[UUID] = None
    purchase_order_id: UUID


class BatchMatchRequest(BaseModel):
    """Request for batch matching."""
    matches: list[BatchMatchItem] = Field(..., min_length=1, max_length=100)


class BatchMatchResultItem(BaseModel):
    """Result of a single batch match item."""
    match_id: Optional[str] = None
    status: Optional[str] = None
    score: Optional[float] = None
    request: Optional[dict] = None
    error: Optional[str] = None


class BatchMatchResponse(BaseModel):
    """Response from batch matching operation."""
    total: int
    successful: int
    failed: int
    auto_approved: int
    pending_review: int
    rejected: int
    results: list[BatchMatchResultItem]


class BalanceResponse(BaseModel):
    """Balance ledger entry response."""
    id: UUID
    document_id: UUID
    document_type: str
    reference_document_id: Optional[UUID]
    reference_document_type: Optional[str]
    original_amount: Decimal
    matched_amount: Decimal
    balance_amount: Decimal
    balance_type: str
    currency: str
    status: str
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MatchStatusEnum(str):
    """Match status enum values."""
    AUTO_APPROVED = "AUTO_APPROVED"
    PENDING_REVIEW = "PENDING_REVIEW"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

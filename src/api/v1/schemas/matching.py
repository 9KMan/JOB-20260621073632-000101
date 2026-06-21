# src/api/v1/schemas/matching.py
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# Matching Line Schemas
class MatchingLineResponse(BaseModel):
    """Schema for matching line response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    item_code: str
    item_description: str
    po_quantity: Decimal
    invoice_quantity: Decimal
    delivery_quantity: Decimal
    matched_quantity: Decimal
    variance_quantity: Decimal
    po_amount: Decimal
    invoice_amount: Decimal
    matched_amount: Decimal
    variance_amount: Decimal
    line_match_score: Decimal
    status: str
    purchase_order_line_id: Optional[UUID] = None
    invoice_line_id: Optional[UUID] = None
    delivery_note_line_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime


# Matching Result Schemas
class MatchingResultBase(BaseModel):
    """Base schema for matching result."""
    invoice_id: Optional[UUID] = None
    delivery_note_id: Optional[UUID] = None
    purchase_order_id: Optional[UUID] = None


class MatchingResultResponse(MatchingResultBase):
    """Schema for matching result response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    line_match_score: Decimal
    amount_match_score: Decimal
    date_match_score: Decimal
    overall_score: Decimal
    po_amount: Decimal
    invoice_amount: Decimal
    variance_amount: Decimal
    status: str
    decision_status: str
    variance_reason: Optional[str] = None
    notes: Optional[str] = None
    reviewed_by_id: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    review_comments: Optional[str] = None
    routing_decision: Optional[str] = None
    auto_approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    lines: List[MatchingLineResponse] = []


class MatchingResultListResponse(BaseModel):
    """Paginated list of matching results."""
    items: List[MatchingResultResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Matching Request Schemas
class MatchInvoiceToPOSchema(BaseModel):
    """Schema for matching invoice to PO."""
    invoice_id: UUID
    purchase_order_id: UUID


class MatchDeliveryNoteToPOSchema(BaseModel):
    """Schema for matching delivery note to PO."""
    delivery_note_id: UUID
    purchase_order_id: UUID


class MatchThreeWaySchema(BaseModel):
    """Schema for 3-way matching."""
    invoice_id: UUID
    delivery_note_id: UUID
    purchase_order_id: UUID


class MatchDocumentsBySupplierSchema(BaseModel):
    """Schema for auto-matching documents by supplier."""
    supplier_id: str
    match_type: str = Field(
        default="three_way",
        pattern="^(invoice_po|deliver_po|invoice_dn|three_way)$"
    )


# Review Schemas
class ReviewDecisionSchema(BaseModel):
    """Schema for reviewing a matching result."""
    decision: str = Field(
        ...,
        pattern="^(confirmed|rejected)$"
    )
    comments: Optional[str] = None


class BatchReviewSchema(BaseModel):
    """Schema for batch review of matching results."""
    matching_result_ids: List[UUID] = Field(..., min_length=1, max_length=50)
    decision: str = Field(
        ...,
        pattern="^(confirmed|rejected)$"
    )
    comments: Optional[str] = None


# Balance Ledger Schemas
class BalanceLedgerResponse(BaseModel):
    """Schema for balance ledger response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    purchase_order_id: UUID
    purchase_order_line_id: Optional[UUID] = None
    document_type: str
    document_id: UUID
    document_number: str
    original_amount: Decimal
    matched_amount: Decimal
    remaining_amount: Decimal
    original_quantity: Decimal
    matched_quantity: Decimal
    remaining_quantity: Decimal
    is_settled: bool
    settlement_date: Optional[date] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# Statistics Schemas
class MatchingStatisticsResponse(BaseModel):
    """Schema for matching statistics."""
    total_matches: int
    auto_approved: int
    pending_review: int
    confirmed: int
    rejected: int
    disputed: int
    average_score: Decimal
    auto_approval_rate: Decimal
    average_variance: Decimal

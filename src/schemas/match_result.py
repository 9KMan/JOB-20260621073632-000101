# src/schemas/match_result.py
"""Match Result Pydantic schemas."""
from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import date

from pydantic import BaseModel, Field


# Match Line Item
class MatchLineItemResponse(BaseModel):
    """Schema for match line item response."""
    
    id: UUID
    match_result_id: UUID
    po_line_item_id: Optional[UUID]
    po_line_number: Optional[str]
    po_sku: Optional[str]
    invoice_line_item_id: Optional[UUID]
    invoice_line_number: Optional[str]
    invoice_sku: Optional[str]
    dn_line_item_id: Optional[UUID]
    dn_line_number: Optional[str]
    dn_sku: Optional[str]
    po_quantity: Optional[Decimal]
    invoice_quantity: Optional[Decimal]
    dn_quantity: Optional[Decimal]
    po_amount: Optional[Decimal]
    invoice_amount: Optional[Decimal]
    dn_amount: Optional[Decimal]
    is_matched: str
    match_type: Optional[str]
    quantity_variance: Decimal
    amount_variance: Decimal
    variance_percentage: Decimal
    match_data: Optional[Dict[str, Any]]
    created_at: str
    updated_at: str
    
    model_config = {"from_attributes": True}


# Match Result
class MatchResultBase(BaseModel):
    """Base schema for match results."""
    
    match_type: str = Field(..., description="Match type")
    match_date: date = Field(..., description="Match date")


class MatchResultCreate(MatchResultBase):
    """Schema for creating match results."""
    
    purchase_order_id: Optional[UUID] = Field(None, description="PO ID")
    invoice_id: Optional[UUID] = Field(None, description="Invoice ID")
    delivery_note_id: Optional[UUID] = Field(None, description="Delivery Note ID")


class MatchResultUpdate(BaseModel):
    """Schema for updating match results."""
    
    match_status: Optional[str] = Field(None, description="Match status")
    decision: Optional[str] = Field(None, description="Decision")
    notes: Optional[str] = Field(None, description="Notes")
    dispute_reason: Optional[str] = Field(None, description="Dispute reason")
    reviewer_comments: Optional[str] = Field(None, description="Reviewer comments")


class MatchDecisionRequest(BaseModel):
    """Schema for making match decisions."""
    
    decision: str = Field(..., description="Decision: CONFIRMED, REJECTED, or PENDING_REVIEW")
    reviewer_comments: Optional[str] = Field(None, description="Reviewer comments")
    dispute_reason: Optional[str] = Field(None, description="Dispute reason if rejected")


class MatchResultResponse(BaseModel):
    """Schema for match result response."""
    
    id: UUID
    purchase_order_id: Optional[UUID]
    invoice_id: Optional[UUID]
    delivery_note_id: Optional[UUID]
    match_type: str
    match_status: str
    confidence_score: Decimal
    decision: Optional[str]
    po_amount: Optional[Decimal]
    invoice_amount: Optional[Decimal]
    dn_amount: Optional[Decimal]
    variance_amount: Decimal
    match_date: date
    decision_date: Optional[date]
    decided_by: Optional[str]
    notes: Optional[str]
    dispute_reason: Optional[str]
    reviewer_comments: Optional[str]
    reviewed_at: Optional[date]
    created_at: str
    updated_at: str
    
    model_config = {"from_attributes": True}


class MatchResultWithDetails(MatchResultResponse):
    """Schema for match result with full details."""
    
    line_items: List[MatchLineItemResponse] = []
    match_details: Optional[Dict[str, Any]] = None
    
    model_config = {"from_attributes": True}


class MatchResultListResponse(BaseModel):
    """Schema for match result list response."""
    
    id: UUID
    match_type: str
    match_status: str
    decision: Optional[str]
    confidence_score: Decimal
    variance_amount: Decimal
    match_date: date
    created_at: str
    
    model_config = {"from_attributes": True}


class MatchRequest(BaseModel):
    """Schema for requesting matches."""
    
    invoice_id: Optional[UUID] = Field(None, description="Invoice ID to match")
    delivery_note_id: Optional[UUID] = Field(None, description="Delivery Note ID to match")
    po_id: Optional[UUID] = Field(None, description="Specific PO ID to match against")
    match_type: Optional[str] = Field(
        None,
        description="Match type: PO_INVOICE, PO_DN, INVOICE_DN, or THREE_WAY"
    )


class MatchSummary(BaseModel):
    """Summary of matching results."""
    
    total_matches: int = Field(..., description="Total number of matches")
    auto_approved: int = Field(..., description="Number auto-approved")
    pending_review: int = Field(..., description="Number pending review")
    rejected: int = Field(..., description="Number rejected")
    average_confidence: Decimal = Field(..., description="Average confidence score")

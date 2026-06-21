// app/schemas/matching.py
"""Matching schemas."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field


class MatchRequest(BaseModel):
    """Schema for initiating 3-way matching."""
    invoice_id: Optional[uuid.UUID] = None
    delivery_note_id: Optional[uuid.UUID] = None
    purchase_order_id: Optional[uuid.UUID] = None
    
    # Matching options
    auto_match: bool = Field(default=True)
    include_partial_matches: bool = Field(default=True)
    
    model_config = {"extra": "forbid"}


class MatchScoreDetail(BaseModel):
    """Schema for individual match score details."""
    product_code: str
    po_quantity: Optional[Decimal] = None
    invoice_quantity: Optional[Decimal] = None
    dn_quantity: Optional[Decimal] = None
    quantity_match: Decimal = Field(..., ge=0, le=1)
    price_match: Decimal = Field(..., ge=0, le=1)
    line_score: Decimal = Field(..., ge=0, le=1)


class MatchResultBase(BaseModel):
    """Base match result schema."""
    line_match_score: Decimal
    amount_match_score: Decimal
    date_match_score: Decimal
    overall_score: Decimal
    status: str
    decision: str
    action: str
    match_type: str
    variance_amount: Decimal
    variance_reason: Optional[str] = None
    line_match_details: Optional[List[Dict[str, Any]]] = None
    matched_at: datetime


class MatchResultResponse(MatchResultBase):
    """Schema for match result response."""
    id: uuid.UUID
    invoice_id: Optional[uuid.UUID] = None
    delivery_note_id: Optional[uuid.UUID] = None
    purchase_order_id: Optional[uuid.UUID] = None
    confirmed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class MatchConfirmationCreate(BaseModel):
    """Schema for confirming a match result."""
    match_result_id: uuid.UUID
    confirmed: bool
    comments: Optional[str] = None


class MatchConfirmationResponse(BaseModel):
    """Schema for match confirmation response."""
    id: uuid.UUID
    match_result_id: uuid.UUID
    confirmed_by_id: uuid.UUID
    confirmed: bool
    final_status: str
    final_action: str
    comments: Optional[str] = None
    confirmed_at: datetime
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class BalanceLedgerResponse(BaseModel):
    """Schema for balance ledger response."""
    id: uuid.UUID
    invoice_id: Optional[uuid.UUID] = None
    delivery_note_id: Optional[uuid.UUID] = None
    purchase_order_id: Optional[uuid.UUID] = None
    original_amount: Decimal
    matched_amount: Decimal
    remaining_amount: Decimal
    product_code: Optional[str] = None
    original_quantity: Optional[Decimal] = None
    matched_quantity: Decimal
    remaining_quantity: Optional[Decimal] = None
    is_settled: bool
    settlement_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class MatchResponse(BaseModel):
    """Schema for match response containing results and balances."""
    match_id: uuid.UUID
    status: str
    match_type: str
    results: List[MatchResultResponse]
    balance_summary: Dict[str, Any]
    decision: str
    action: str

# app/schemas/matching.py
"""Matching schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class MatchLineResultResponse(BaseModel):
    """Match line result response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    invoice_line_id: Optional[str] = None
    po_line_id: Optional[str] = None
    dn_line_id: Optional[str] = None
    match_type: str
    match_score: Decimal
    product_match: str
    quantity_match: str
    amount_match: str
    invoice_quantity: Optional[Decimal] = None
    po_quantity: Optional[Decimal] = None
    dn_quantity: Optional[Decimal] = None
    quantity_variance: Optional[Decimal] = None
    invoice_line_amount: Optional[Decimal] = None
    po_line_amount: Optional[Decimal] = None
    dn_line_amount: Optional[Decimal] = None
    amount_variance: Optional[Decimal] = None
    match_details: Optional[Dict[str, Any]] = None
    created_at: datetime


class MatchingResponse(BaseModel):
    """Matching result response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    invoice_id: str
    po_id: Optional[str] = None
    dn_id: Optional[str] = None
    match_type: str
    total_score: Decimal
    line_score: Decimal
    amount_score: Decimal
    date_score: Decimal
    status: str
    decision: Optional[str] = None
    invoice_amount: Decimal
    po_amount: Optional[Decimal] = None
    dn_amount: Optional[Decimal] = None
    variance_amount: Decimal
    variance_details: Optional[Dict[str, Any]] = None
    confirmed_by: Optional[str] = None
    confirmed_at: Optional[str] = None
    confirmation_notes: Optional[str] = None
    error_message: Optional[str] = None
    warnings: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime
    line_results: List[MatchLineResultResponse] = []


class MatchingResultListResponse(BaseModel):
    """Matching result list response with pagination."""

    items: List[MatchingResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class MatchConfirmationRequest(BaseModel):
    """Match confirmation request."""

    status: str = Field(..., pattern="^(confirmed|rejected)$")
    notes: Optional[str] = None


class MatchingRequest(BaseModel):
    """Matching request for manual matching."""

    invoice_id: str
    po_id: Optional[str] = None
    dn_id: Optional[str] = None

// src/schemas/match.py
"""
FinaRo AP Automation Core Engine
Match Pydantic Schemas
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.base import BaseSchema


class MatchResultBase(BaseSchema):
    """Base schema for Match Result."""
    po_line_id: Optional[UUID] = None
    invoice_line_id: Optional[UUID] = None
    dn_line_id: Optional[UUID] = None
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    po_quantity: Decimal = Field(default=Decimal('0'))
    invoice_quantity: Decimal = Field(default=Decimal('0'))
    dn_quantity: Decimal = Field(default=Decimal('0'))
    matched_quantity: Decimal = Field(default=Decimal('0'))
    variance_quantity: Decimal = Field(default=Decimal('0'))
    po_amount: Decimal = Field(default=Decimal('0'))
    invoice_amount: Decimal = Field(default=Decimal('0'))
    dn_amount: Decimal = Field(default=Decimal('0'))
    matched_amount: Decimal = Field(default=Decimal('0'))
    variance_amount: Decimal = Field(default=Decimal('0'))
    score: Decimal = Field(default=Decimal('0'))
    match_type: Optional[str] = None
    variance_reason: Optional[str] = None
    variance_tolerance: Decimal = Field(default=Decimal('0'))
    notes: Optional[str] = None


class MatchResultCreate(MatchResultBase):
    """Schema for creating a Match Result."""
    pass


class MatchResultUpdate(BaseSchema):
    """Schema for updating a Match Result."""
    status: Optional[str] = None
    matched_quantity: Optional[Decimal] = Field(None, ge=Decimal('0'))
    matched_amount: Optional[Decimal] = Field(None, ge=Decimal('0'))
    variance_reason: Optional[str] = None
    notes: Optional[str] = None


class MatchResultResponse(MatchResultBase):
    """Schema for Match Result response."""
    id: UUID
    match_id: UUID
    status: str
    match_percentage: Decimal
    is_within_tolerance: bool
    created_at: datetime
    updated_at: datetime


class MatchBase(BaseSchema):
    """Base schema for Match."""
    po_id: Optional[UUID] = None
    invoice_id: Optional[UUID] = None
    dn_id: Optional[UUID] = None
    match_type: str
    matched_lines: Optional[List[dict]] = None
    variance_reason: Optional[str] = None
    variance_notes: Optional[str] = None


class MatchCreate(MatchBase):
    """Schema for creating a Match."""
    results: List[MatchResultCreate] = Field(default_factory=list)


class MatchUpdate(BaseSchema):
    """Schema for updating a Match."""
    status: Optional[str] = None
    decision: Optional[str] = None
    variance_reason: Optional[str] = None
    variance_notes: Optional[str] = None
    approval_comments: Optional[str] = None
    review_comments: Optional[str] = None


class MatchDecisionRequest(BaseSchema):
    """Schema for match decision request."""
    decision: str = Field(..., pattern="^(AUTO_APPROVED|HUMAN_REVIEW|REJECTED|DISPUTE)$")
    comments: Optional[str] = None
    dispute_reason: Optional[str] = None


class MatchResponse(MatchBase):
    """Schema for Match response."""
    id: UUID
    match_number: str
    status: str
    decision: str
    total_score: Decimal
    line_score: Decimal
    amount_score: Decimal
    date_score: Decimal
    po_amount: Decimal
    invoice_amount: Decimal
    dn_amount: Decimal
    variance_amount: Decimal
    quantity_po: Decimal
    quantity_invoice: Decimal
    quantity_dn: Decimal
    variance_quantity: Decimal
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    is_confirmed: bool
    is_pending: bool
    is_rejected: bool
    results: List[MatchResultResponse]
    created_at: datetime
    updated_at: datetime
    
    @field_validator('results', mode='before')
    @classmethod
    def validate_results(cls, v):
        if v is None:
            return []
        return v


class MatchListResponse(BaseSchema):
    """Schema for Match list item response."""
    id: UUID
    match_number: str
    match_type: str
    po_id: Optional[UUID]
    invoice_id: Optional[UUID]
    dn_id: Optional[UUID]
    status: str
    decision: str
    total_score: Decimal
    variance_amount: Decimal
    is_confirmed: bool
    is_pending: bool
    created_at: datetime

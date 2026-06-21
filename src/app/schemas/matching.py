# src/app/schemas/matching.py
"""Matching schemas."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.app.schemas.common import BaseSchema, TimestampMixin, UUIDMixin
from src.app.models.enums import MatchStatus, MatchResultType, DecisionType


class CrossReferenceBase(BaseSchema):
    """Base cross-reference schema."""
    invoice_line_id: Optional[UUID] = None
    po_line_id: Optional[UUID] = None
    dn_line_id: Optional[UUID] = None
    quantity_matched: Decimal = Field(..., ge=0)
    amount_matched: Decimal = Field(..., ge=0)
    match_confidence: Decimal = Field(..., ge=0, le=1)


class CrossReferenceCreate(CrossReferenceBase):
    """Schema for creating a cross-reference."""
    match_result_id: UUID


class CrossReferenceRead(UUIDMixin, TimestampMixin, CrossReferenceBase):
    """Schema for reading a cross-reference."""
    match_result_id: UUID
    deleted_at: Optional[datetime] = None
    is_deleted: bool = False


class MatchResultBase(BaseSchema):
    """Base match result schema."""
    invoice_id: UUID
    delivery_note_id: Optional[UUID] = None
    po_id: Optional[UUID] = None
    line_level_score: Decimal = Field(..., ge=0, le=1)
    amount_score: Decimal = Field(..., ge=0, le=1)
    date_score: Decimal = Field(..., ge=0, le=1)
    total_score: Decimal = Field(..., ge=0, le=1)
    match_type: MatchResultType
    invoice_amount: Decimal = Field(..., ge=0)
    po_amount: Optional[Decimal] = None
    amount_difference: Decimal = Field(default=Decimal("0.00"))
    notes: Optional[str] = None
    variance_reason: Optional[str] = None


class MatchResultCreate(MatchResultBase):
    """Schema for creating a match result."""
    cross_references: list[CrossReferenceCreate] = Field(default_factory=list)


class MatchResultUpdate(BaseSchema):
    """Schema for updating a match result."""
    status: Optional[MatchStatus] = None
    notes: Optional[str] = None
    variance_reason: Optional[str] = None


class MatchResultRead(UUIDMixin, TimestampMixin, MatchResultBase):
    """Schema for reading a match result."""
    status: MatchStatus
    deleted_at: Optional[datetime] = None
    is_deleted: bool = False
    cross_references: list[CrossReferenceRead] = Field(default_factory=list)


class MatchDecisionBase(BaseSchema):
    """Base match decision schema."""
    match_result_id: UUID
    decision: DecisionType
    comments: Optional[str] = None
    reason: Optional[str] = None


class MatchDecisionCreate(MatchDecisionBase):
    """Schema for creating a match decision."""
    pass


class MatchDecisionRead(UUIDMixin, TimestampMixin, MatchDecisionBase):
    """Schema for reading a match decision."""
    reviewed_by: Optional[UUID] = None
    previous_status: MatchStatus
    new_status: MatchStatus


class MatchScoreBreakdown(BaseModel):
    """Detailed match score breakdown."""
    line_level_score: Decimal
    amount_score: Decimal
    date_score: Decimal
    total_score: Decimal
    weight_line_level: Decimal
    weight_amount: Decimal
    weight_date: Decimal


class MatchAnalysisResult(BaseModel):
    """Result of a match analysis."""
    match_result: MatchResultRead
    score_breakdown: MatchScoreBreakdown
    recommendations: list[str] = Field(default_factory=list)

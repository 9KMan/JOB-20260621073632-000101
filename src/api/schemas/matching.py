// src/api/schemas/matching.py
"""Matching-related schemas."""
import decimal
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from src.models.matching import MatchConfidence, MatchDecision, MatchResult


class MatchScoreResponse(BaseModel):
    """Schema for match score breakdown."""

    line_score: decimal.Decimal = Field(..., description="Line-level match score")
    amount_score: decimal.Decimal = Field(..., description="Amount match score")
    date_score: decimal.Decimal = Field(..., description="Date match score")
    overall_score: decimal.Decimal = Field(..., description="Overall match score")
    confidence: MatchConfidence = Field(..., description="Match confidence level")


class MatchingRecordResponse(BaseModel):
    """Schema for matching record response."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Record ID")
    document_id: str = Field(..., description="Primary document ID")
    matched_document_id: str = Field(..., description="Matched document ID")
    matched_document_number: str | None = Field(default=None, description="Matched document number")
    matched_document_type: str | None = Field(default=None, description="Matched document type")
    match_type: str = Field(..., description="Match type")
    score: MatchScoreResponse = Field(..., description="Match scores")
    confidence: MatchConfidence = Field(..., description="Match confidence")
    decision: MatchDecision = Field(..., description="Match decision")
    result: MatchResult = Field(..., description="Match result")
    matched_line_count: int = Field(..., description="Number of matched lines")
    total_line_count: int = Field(..., description="Total number of lines")
    matched_amount: decimal.Decimal = Field(..., description="Matched amount")
    balance_after_match: decimal.Decimal = Field(..., description="Balance after match")
    is_confirmed: bool = Field(..., description="Is confirmed by human")
    reviewed_by: str | None = Field(default=None, description="Reviewer ID")
    reviewed_at: date | None = Field(default=None, description="Review timestamp")
    review_notes: str | None = Field(default=None, description="Review notes")
    created_at: datetime = Field(..., description="Creation timestamp")


class MatchResultResponse(BaseModel):
    """Schema for complete match result."""

    model_config = ConfigDict(from_attributes=True)

    document_id: str = Field(..., description="Document ID")
    document_number: str = Field(..., description="Document number")
    document_type: str = Field(..., description="Document type")
    status: str = Field(..., description="Document status")
    overall_score: decimal.Decimal = Field(..., description="Overall match score")
    result: MatchResult = Field(..., description="Match result")
    matches: list[MatchingRecordResponse] = Field(default_factory=list, description="Matching records")
    total_matches: int = Field(..., description="Total number of matches")
    confirmed_matches: int = Field(..., description="Number of confirmed matches")
    pending_matches: int = Field(..., description="Number of pending matches")


class MatchReviewRequest(BaseModel):
    """Schema for reviewing a match."""

    decision: MatchDecision = Field(..., description="Review decision")
    notes: str | None = Field(default=None, description="Review notes")


class MatchResultDetailResponse(BaseModel):
    """Schema for detailed match result with line-level breakdown."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Record ID")
    document_id: str = Field(..., description="Document ID")
    matched_document_id: str = Field(..., description="Matched document ID")
    match_type: str = Field(..., description="Match type")
    score: MatchScoreResponse = Field(..., description="Match scores")
    matched_line_ids: list[str] = Field(default_factory=list, description="Matched line IDs")
    line_matches: list[dict] = Field(default_factory=list, description="Line-level matches")
    created_at: datetime = Field(..., description="Creation timestamp")

// src/schemas/matching.py
"""Matching schemas."""
import uuid
import decimal
from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict

from src.models.enums import MatchStatus, MatchDecision, DocumentType


class MatchRecordBase(BaseModel):
    """Base schema for Match Record."""
    match_type: str
    matched_quantity: decimal.Decimal
    matched_amount: decimal.Decimal
    line_match_score: decimal.Decimal
    amount_match_score: decimal.Decimal
    date_match_score: decimal.Decimal
    total_match_score: decimal.Decimal
    quantity_variance: decimal.Decimal
    amount_variance: decimal.Decimal


class MatchRecordCreate(MatchRecordBase):
    """Schema for creating a Match Record."""
    invoice_id: Optional[uuid.UUID] = None
    invoice_line_id: Optional[uuid.UUID] = None
    delivery_note_id: Optional[uuid.UUID] = None
    delivery_note_line_id: Optional[uuid.UUID] = None
    purchase_order_id: Optional[uuid.UUID] = None
    purchase_order_line_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None


class MatchRecordUpdate(BaseModel):
    """Schema for updating a Match Record."""
    matched_quantity: Optional[decimal.Decimal] = None
    matched_amount: Optional[decimal.Decimal] = None
    line_match_score: Optional[decimal.Decimal] = None
    amount_match_score: Optional[decimal.Decimal] = None
    date_match_score: Optional[decimal.Decimal] = None
    total_match_score: Optional[decimal.Decimal] = None
    status: Optional[MatchStatus] = None
    decision: Optional[MatchDecision] = None
    decision_reason: Optional[str] = None
    quantity_variance: Optional[decimal.Decimal] = None
    amount_variance: Optional[decimal.Decimal] = None
    notes: Optional[str] = None


class MatchRecordResponse(MatchRecordBase):
    """Schema for Match Record response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    invoice_id: Optional[uuid.UUID] = None
    invoice_line_id: Optional[uuid.UUID] = None
    delivery_note_id: Optional[uuid.UUID] = None
    delivery_note_line_id: Optional[uuid.UUID] = None
    purchase_order_id: Optional[uuid.UUID] = None
    purchase_order_line_id: Optional[uuid.UUID] = None
    status: MatchStatus
    decision: Optional[MatchDecision] = None
    decision_reason: Optional[str] = None
    decided_at: Optional[datetime] = None
    decided_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime


class MatchDecisionRequest(BaseModel):
    """Schema for making a match decision."""
    match_record_id: uuid.UUID
    decision: MatchDecision
    decision_reason: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = Field(None, max_length=500)


class BalanceLedgerResponse(BaseModel):
    """Schema for Balance Ledger response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_type: DocumentType
    document_id: uuid.UUID
    document_line_id: Optional[uuid.UUID] = None
    purchase_order_id: Optional[uuid.UUID] = None
    purchase_order_line_id: Optional[uuid.UUID] = None
    invoice_id: Optional[uuid.UUID] = None
    invoice_line_id: Optional[uuid.UUID] = None
    delivery_note_id: Optional[uuid.UUID] = None
    delivery_note_line_id: Optional[uuid.UUID] = None
    original_quantity: decimal.Decimal
    matched_quantity: decimal.Decimal
    outstanding_quantity: decimal.Decimal
    original_amount: decimal.Decimal
    matched_amount: decimal.Decimal
    outstanding_amount: decimal.Decimal
    is_outstanding: bool
    last_match_date: Optional[date] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class MatchingResult(BaseModel):
    """Schema for matching operation result."""
    success: bool
    match_records: List[MatchRecordResponse] = Field(default_factory=list)
    decision: Optional[MatchDecision] = None
    message: str
    total_match_score: Optional[decimal.Decimal] = None
    auto_approved: bool = False
    pending_review: bool = False
    disputed: bool = False

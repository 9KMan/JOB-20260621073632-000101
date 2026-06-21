# src/schemas/matching.py
"""Matching schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MatchingLineBase(BaseModel):
    """Base matching line schema."""
    line_number: int
    po_line_id: Optional[UUID] = None
    invoice_line_id: Optional[UUID] = None
    dn_line_id: Optional[UUID] = None
    item_code: Optional[str] = None
    item_description: Optional[str] = None
    po_quantity: Optional[Decimal] = None
    invoice_quantity: Optional[Decimal] = None
    dn_quantity: Optional[Decimal] = None
    quantity_variance: Decimal = Field(default=Decimal("0"))
    po_amount: Optional[Decimal] = None
    invoice_amount: Optional[Decimal] = None
    dn_amount: Optional[Decimal] = None
    amount_variance: Decimal = Field(default=Decimal("0"))
    match_status: str = "pending"
    match_type: Optional[str] = None


class MatchingLineCreate(MatchingLineBase):
    """Matching line creation schema."""
    pass


class MatchingLineUpdate(BaseModel):
    """Matching line update schema."""
    match_status: Optional[str] = None
    match_type: Optional[str] = None


class MatchingLineInDB(MatchingLineBase):
    """Matching line database schema."""
    id: UUID
    matching_record_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MatchingLineResponse(MatchingLineBase):
    """Matching line response schema."""
    id: UUID
    matching_record_id: UUID

    model_config = ConfigDict(from_attributes=True)


class MatchingRecordBase(BaseModel):
    """Base matching record schema."""
    purchase_order_id: Optional[UUID] = None
    invoice_id: Optional[UUID] = None
    delivery_note_id: Optional[UUID] = None
    match_type: str
    match_status: str = "pending"
    decision: str = "HUMAN_REVIEW"
    decision_reason: Optional[str] = None
    line_weight: Decimal = Field(default=Decimal("70"))
    amount_weight: Decimal = Field(default=Decimal("20"))
    date_weight: Decimal = Field(default=Decimal("10"))
    match_metadata: Optional[Dict[str, Any]] = None


class MatchingRecordCreate(MatchingRecordBase):
    """Matching record creation schema."""
    line_matches: List[MatchingLineCreate] = []


class MatchingRecordUpdate(BaseModel):
    """Matching record update schema."""
    match_status: Optional[str] = None
    decision: Optional[str] = None
    decision_reason: Optional[str] = None


class MatchingRecordInDB(MatchingRecordBase):
    """Matching record database schema."""
    id: UUID
    line_level_score: Decimal
    amount_score: Decimal
    date_score: Decimal
    overall_score: Decimal
    po_amount: Optional[Decimal] = None
    invoice_amount: Optional[Decimal] = None
    delivery_note_amount: Optional[Decimal] = None
    variance_amount: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MatchingRecordResponse(MatchingRecordBase):
    """Matching record response schema."""
    id: UUID
    line_level_score: Decimal
    amount_score: Decimal
    date_score: Decimal
    overall_score: Decimal
    po_amount: Optional[Decimal] = None
    invoice_amount: Optional[Decimal] = None
    delivery_note_amount: Optional[Decimal] = None
    variance_amount: Decimal
    line_matches: List[MatchingLineResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MatchingRecordListResponse(BaseModel):
    """Matching record list response schema."""
    items: List[MatchingRecordResponse]
    total: int
    page: int
    page_size: int


class MatchingResultResponse(BaseModel):
    """Matching result response schema."""
    confirmed: List[MatchingRecordResponse]
    pending: List[MatchingRecordResponse]
    rejected: List[MatchingRecordResponse]
    total_processed: int

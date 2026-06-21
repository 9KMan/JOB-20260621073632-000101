# src/schemas/matching.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class MatchingResultBase(BaseModel):
    """Base schema for Matching Result."""
    invoice_id: Optional[str] = None
    dn_id: Optional[str] = None
    po_id: Optional[str] = None


class MatchingResultCreate(MatchingResultBase):
    """Schema for creating Matching Result."""
    pass


class MatchingResultUpdate(BaseModel):
    """Schema for updating Matching Result."""
    status: Optional[str] = None
    notes: Optional[str] = None


class MatchingResultResponse(MatchingResultBase):
    """Schema for Matching Result response."""
    id: str
    invoice_po_score: Optional[Decimal] = None
    dn_po_score: Optional[Decimal] = None
    invoice_dn_score: Optional[Decimal] = None
    overall_score: Decimal
    invoice_amount: Optional[Decimal] = None
    po_amount: Optional[Decimal] = None
    dn_amount: Optional[Decimal] = None
    variance_amount: Decimal
    variance_percentage: Decimal
    status: str
    match_type: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MatchDecisionBase(BaseModel):
    """Base schema for Match Decision."""
    decision_type: str
    decision_notes: Optional[str] = None


class MatchDecisionCreate(MatchDecisionBase):
    """Schema for creating Match Decision."""
    matching_result_id: str


class MatchDecisionUpdate(BaseModel):
    """Schema for updating Match Decision."""
    decision_notes: Optional[str] = None


class MatchDecisionResponse(MatchDecisionBase):
    """Schema for Match Decision response."""
    id: str
    matching_result_id: str
    decided_by: Optional[str] = None
    previous_status: Optional[str] = None
    new_status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BalanceLedgerBase(BaseModel):
    """Base schema for Balance Ledger."""
    invoice_id: Optional[str] = None
    dn_id: Optional[str] = None
    po_id: Optional[str] = None
    matching_result_id: Optional[str] = None
    document_type: str
    document_number: str
    original_amount: Decimal
    currency: str = "USD"
    notes: Optional[str] = None


class BalanceLedgerCreate(BalanceLedgerBase):
    """Schema for creating Balance Ledger."""
    matched_amount: Optional[Decimal] = None


class BalanceEntryCreate(BaseModel):
    """Schema for creating a balance entry."""
    document_type: str = Field(..., description="Type: invoice, dn, or po")
    document_id: str
    document_number: str
    amount: Decimal
    currency: str = "USD"


class BalanceLedgerResponse(BalanceLedgerBase):
    """Schema for Balance Ledger response."""
    id: str
    matched_amount: Decimal
    remaining_balance: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MatchRequest(BaseModel):
    """Schema for requesting a match operation."""
    invoice_id: Optional[str] = None
    dn_id: Optional[str] = None
    po_id: Optional[str] = None
    match_type: str = Field(
        default="auto",
        description="Type: auto, invoice_po, dn_po, invoice_dn, three_way"
    )


class MatchResponse(BaseModel):
    """Schema for match operation response."""
    success: bool
    matching_result: Optional[MatchingResultResponse] = None
    message: str
    decision: Optional[str] = None

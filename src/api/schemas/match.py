// src/api/schemas/match.py
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from src.models.match import MatchStatus, MatchDecision


class MatchLineBase(BaseModel):
    product_code: str
    invoice_quantity: Optional[Decimal] = None
    po_quantity: Optional[Decimal] = None
    dn_quantity: Optional[Decimal] = None
    line_match_score: Decimal
    quantity_variance: Decimal


class MatchLineResponse(MatchLineBase):
    id: UUID
    invoice_line_id: Optional[UUID] = None
    po_line_id: Optional[UUID] = None
    dn_line_id: Optional[UUID] = None
    
    class Config:
        from_attributes = True


class MatchBase(BaseModel):
    invoice_id: UUID
    delivery_note_id: Optional[UUID] = None
    purchase_order_id: UUID


class MatchCreate(MatchBase):
    pass


class MatchResponse(MatchBase):
    id: UUID
    match_type: str
    match_score: Decimal
    status: MatchStatus
    decision: Optional[MatchDecision] = None
    invoice_amount: Decimal
    po_amount: Decimal
    variance_amount: Decimal
    confirmed_by: Optional[UUID] = None
    confirmed_at: Optional[datetime] = None
    created_at: datetime
    lines: List[MatchLineResponse] = []
    
    class Config:
        from_attributes = True


class MatchConfirmRequest(BaseModel):
    confirm: bool
    notes: Optional[str] = None


class MatchQueryParams(BaseModel):
    invoice_id: Optional[UUID] = None
    purchase_order_id: Optional[UUID] = None
    delivery_note_id: Optional[UUID] = None
    status: Optional[MatchStatus] = None
    decision: Optional[MatchDecision] = None

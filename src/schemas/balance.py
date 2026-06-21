// src/schemas/balance.py
"""
FinaRo AP Automation Core Engine
Balance Ledger Pydantic Schemas
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.base import BaseSchema


class BalanceLedgerBase(BaseSchema):
    """Base schema for Balance Ledger."""
    document_type: str = Field(..., pattern="^(PO|Invoice|DN)$")
    document_id: UUID
    document_number: str
    line_id: Optional[UUID] = None
    line_number: Optional[str] = None
    balance_type: str
    direction: str = Field(default="DEBIT", pattern="^(DEBIT|CREDIT)$")
    product_id: Optional[UUID] = None
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    original_quantity: Decimal = Field(default=Decimal('0'))
    matched_quantity: Decimal = Field(default=Decimal('0'))
    remaining_quantity: Decimal = Field(default=Decimal('0'))
    original_amount: Decimal = Field(default=Decimal('0'))
    matched_amount: Decimal = Field(default=Decimal('0'))
    remaining_amount: Decimal = Field(default=Decimal('0'))
    currency: str = Field(default="USD", max_length=3)
    effective_date: date
    maturity_date: Optional[date] = None
    notes: Optional[str] = None
    related_balance_id: Optional[UUID] = None
    match_id: Optional[UUID] = None


class BalanceLedgerCreate(BalanceLedgerBase):
    """Schema for creating a Balance Ledger entry."""
    ledger_number: Optional[str] = None


class BalanceLedgerUpdate(BaseSchema):
    """Schema for updating a Balance Ledger entry."""
    remaining_quantity: Optional[Decimal] = Field(None, ge=Decimal('0'))
    remaining_amount: Optional[Decimal] = Field(None, ge=Decimal('0'))
    matched_quantity: Optional[Decimal] = Field(None, ge=Decimal('0'))
    matched_amount: Optional[Decimal] = Field(None, ge=Decimal('0'))
    status: Optional[str] = None
    notes: Optional[str] = None
    resolved_by: Optional[UUID] = None
    resolution_notes: Optional[str] = None


class BalanceLedgerResponse(BalanceLedgerBase):
    """Schema for Balance Ledger response."""
    id: UUID
    ledger_number: str
    status: str
    is_closed: bool
    utilization_percentage: Decimal
    resolved_by: Optional[UUID] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class BalanceLedgerListResponse(BaseSchema):
    """Schema for Balance Ledger list item response."""
    id: UUID
    ledger_number: str
    document_type: str
    document_id: UUID
    document_number: str
    balance_type: str
    remaining_amount: Decimal
    status: str
    is_closed: bool
    currency: str
    effective_date: date
    created_at: datetime


class BalanceSummaryResponse(BaseSchema):
    """Schema for balance summary."""
    total_open: int
    total_partial: int
    total_closed: int
    total_amount_open: Decimal
    total_amount_partial: Decimal
    by_document_type: dict

// src/schemas/balance.py
"""Balance schemas for tracking partial matches."""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import ConfigDict, Field

from src.schemas.common import BaseSchema, PaginatedResponse


class BalanceBase(BaseSchema):
    """Base schema for Balances."""

    purchase_order_id: UUID
    invoice_id: Optional[UUID] = None
    delivery_note_id: Optional[UUID] = None
    balance_type: str = Field(..., max_length=20)
    direction: str = Field(..., max_length=30)
    product_code: Optional[str] = Field(None, max_length=100)
    po_quantity: Decimal = Field(default=Decimal("0"), ge=0)
    matched_quantity: Decimal = Field(default=Decimal("0"), ge=0)
    remaining_quantity: Decimal = Field(default=Decimal("0"), ge=0)
    po_amount: Decimal = Field(default=Decimal("0"), ge=0)
    matched_amount: Decimal = Field(default=Decimal("0"), ge=0)
    remaining_amount: Decimal = Field(default=Decimal("0"), ge=0)
    is_resolved: bool = Field(default=False)
    resolved_at: Optional[UUID] = None
    notes: Optional[str] = Field(None, max_length=500)


class BalanceCreate(BalanceBase):
    """Schema for creating Balances."""

    pass


class BalanceUpdate(BaseSchema):
    """Schema for updating Balances."""

    matched_quantity: Optional[Decimal] = Field(None, ge=0)
    remaining_quantity: Optional[Decimal] = Field(None, ge=0)
    matched_amount: Optional[Decimal] = Field(None, ge=0)
    remaining_amount: Optional[Decimal] = Field(None, ge=0)
    is_resolved: Optional[bool] = None
    resolved_at: Optional[UUID] = None
    notes: Optional[str] = Field(None, max_length=500)


class BalanceResponse(BalanceBase):
    """Schema for Balance responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class BalanceListResponse(PaginatedResponse[BalanceResponse]):
    """Schema for paginated Balance list response."""

    pass


class BalanceSummary(BaseSchema):
    """Schema for Balance summary (minimal data)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    purchase_order_id: UUID
    balance_type: str
    direction: str
    remaining_quantity: Decimal
    remaining_amount: Decimal
    is_resolved: bool

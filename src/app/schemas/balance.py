// src/app/schemas/balance.py
"""Balance schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import BaseSchema, TimestampMixin, UUIDMixin


class BalanceBase(BaseModel):
    """Balance base schema."""

    document_type: str
    document_id: UUID
    document_line_id: Optional[UUID] = None
    balance_type: str
    original_amount: Decimal
    matched_amount: Decimal = Field(default=Decimal("0.00"))
    remaining_amount: Decimal
    original_quantity: Optional[Decimal] = None
    matched_quantity: Optional[Decimal] = Field(default=Decimal("0.00"))
    remaining_quantity: Optional[Decimal] = None
    is_settled: bool = False
    settled_date: Optional[date] = None
    matched_document_type: Optional[str] = None
    matched_document_id: Optional[UUID] = None


class BalanceCreate(BalanceBase):
    """Balance creation schema."""

    pass


class BalanceUpdate(BaseModel):
    """Balance update schema."""

    matched_amount: Optional[Decimal] = None
    remaining_amount: Optional[Decimal] = None
    matched_quantity: Optional[Decimal] = None
    remaining_quantity: Optional[Decimal] = None
    is_settled: Optional[bool] = None
    settled_date: Optional[date] = None
    matched_document_type: Optional[str] = None
    matched_document_id: Optional[UUID] = None


class BalanceResponse(BalanceBase, UUIDMixin, TimestampMixin):
    """Balance response schema."""

    model_config = ConfigDict(from_attributes=True)

    match_percentage: float


class BalanceListResponse(BaseModel):
    """Balance list response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    document_type: str
    document_id: str
    balance_type: str
    remaining_amount: Decimal
    is_settled: bool
    created_at: datetime

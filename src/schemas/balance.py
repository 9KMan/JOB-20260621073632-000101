# src/schemas/balance.py
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from src.schemas.common import TimestampMixinSchema, UUIDMixinSchema


class BalanceBase(BaseModel):
    """Base schema for Balances."""
    balance_type: str
    reference_type: str
    reference_id: str
    original_amount: Decimal = Field(ge=0)
    matched_amount: Decimal = Field(ge=0, default=Decimal("0.00"))
    remaining_amount: Decimal = Field(ge=0)
    is_settled: bool = False
    settlement_date: Optional[date] = None
    purchase_order_id: Optional[str] = None


class BalanceCreate(BalanceBase):
    """Schema for creating Balances."""
    pass


class BalanceUpdate(BaseModel):
    """Schema for updating Balances."""
    matched_amount: Optional[Decimal] = None
    remaining_amount: Optional[Decimal] = None
    is_settled: Optional[bool] = None
    settlement_date: Optional[date] = None


class BalanceResponse(BalanceBase, UUIDMixinSchema, TimestampMixinSchema):
    """Schema for Balance response."""
    
    model_config = {"from_attributes": True}

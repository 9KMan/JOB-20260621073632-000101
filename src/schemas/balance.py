// src/schemas/balance.py
"""Balance Ledger-related Pydantic schemas."""

from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.base import BaseSchema, TimestampMixin


class BalanceLedgerBase(BaseSchema):
    """Base balance ledger schema."""

    balance_type: str
    transaction_type: str
    transaction_date: date
    reference_number: Optional[str] = None
    original_amount: Decimal
    previous_balance: Decimal = Decimal("0.00")
    transaction_amount: Decimal
    current_balance: Decimal
    line_number: Optional[int] = None
    sku: Optional[str] = None
    quantity: Optional[Decimal] = None
    description: Optional[str] = None


class BalanceLedgerCreate(BalanceLedgerBase):
    """Schema for creating a balance ledger entry."""

    purchase_order_id: Optional[UUID] = None
    invoice_id: Optional[UUID] = None
    delivery_note_id: Optional[UUID] = None
    match_id: Optional[UUID] = None


class BalanceLedgerResponse(BalanceLedgerBase, TimestampMixin):
    """Schema for balance ledger response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    purchase_order_id: Optional[UUID] = None
    invoice_id: Optional[UUID] = None
    delivery_note_id: Optional[UUID] = None
    match_id: Optional[UUID] = None


class BalanceSummary(BaseSchema):
    """Schema for balance summary."""

    po_open_balance: Decimal
    po_invoiced_balance: Decimal
    po_delivered_balance: Decimal
    invoice_open_balance: Decimal
    invoice_matched_balance: Decimal
    invoice_paid_balance: Decimal
    total_po_balance: Decimal
    total_invoice_balance: Decimal


class BalanceBySupplier(BaseSchema):
    """Schema for balance breakdown by supplier."""

    supplier_id: UUID
    supplier_code: str
    supplier_name: str
    po_open_balance: Decimal
    invoice_open_balance: Decimal
    variance: Decimal


class TransactionHistory(BaseSchema):
    """Schema for transaction history."""

    date: date
    transaction_type: str
    reference_number: Optional[str] = None
    description: Optional[str] = None
    amount: Decimal
    balance_after: Decimal

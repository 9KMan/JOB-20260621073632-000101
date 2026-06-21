// src/app/schemas/balance.py
"""Balance ledger schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BalanceLedgerBase(BaseModel):
    """Base balance ledger schema."""

    purchase_order_id: UUID
    balance_type: str = Field(..., max_length=50)
    source_document_type: str = Field(..., max_length=50)
    source_document_id: UUID
    original_amount: Decimal = Field(..., ge=0)
    remaining_amount: Decimal = Field(..., ge=0)
    applied_amount: Decimal = Field(default=Decimal("0"), ge=0)
    currency: str = Field(default="USD", max_length=3)
    is_settled: bool = False
    settled_at: Optional[UUID] = None
    match_id: Optional[UUID] = None


class BalanceLedgerCreate(BalanceLedgerBase):
    """Schema for creating a balance ledger entry."""

    pass


class BalanceLedgerUpdate(BaseModel):
    """Schema for updating a balance ledger entry."""

    remaining_amount: Optional[Decimal] = Field(None, ge=0)
    applied_amount: Optional[Decimal] = Field(None, ge=0)
    is_settled: Optional[bool] = None
    settled_at: Optional[UUID] = None
    match_id: Optional[UUID] = None


class BalanceLedgerResponse(BalanceLedgerBase):
    """Balance ledger response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class BalanceLedgerDetailResponse(BalanceLedgerResponse):
    """Balance ledger detail response."""

    po_number: Optional[str] = None
    source_document_number: Optional[str] = None


class BalanceLedgerListResponse(BaseModel):
    """Schema for balance ledger list response."""

    items: list[BalanceLedgerDetailResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class PurchaseOrderBalanceSummary(BaseModel):
    """Purchase order balance summary."""

    purchase_order_id: UUID
    po_number: str
    po_amount: Decimal
    total_invoiced: Decimal
    total_delivered: Decimal
    open_balance: Decimal
    invoice_balance: Decimal
    delivery_balance: Decimal
    currency: str


class SupplierBalanceSummary(BaseModel):
    """Supplier balance summary for payables aging."""

    supplier_id: UUID
    supplier_name: str
    supplier_code: str
    total_open: Decimal
    total_30_days: Decimal
    total_60_days: Decimal
    total_90_plus: Decimal
    currency: str

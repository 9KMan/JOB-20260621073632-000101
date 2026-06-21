// models/balance.py
"""Balance tracking for partial matches."""

import uuid
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Column, String, Numeric, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database import Base
from models.base import BaseModel

if TYPE_CHECKING:
    from models.purchase_order import PurchaseOrder
    from models.invoice import Invoice
    from models.delivery_note import DeliveryNote


class BalanceType(str, Enum):
    """Balance type enumeration."""
    INVOICE = "invoice"
    DELIVERY = "delivery"
    PARTIAL_INVOICE = "partial_invoice"
    PARTIAL_DELIVERY = "partial_delivery"


class Balance(Base, BaseModel):
    """Balance ledger for tracking partial matches and balances across documents."""

    __tablename__ = "balances"

    # Document reference
    document_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # invoice, delivery, PO
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    document_number: Mapped[str] = mapped_column(String(50), nullable=False)

    # Balance type
    balance_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)

    # Original amounts
    original_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    original_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)

    # Matched amounts (cumulative)
    matched_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    matched_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), default=Decimal("0.000"), nullable=False)

    # Remaining balance
    remaining_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    remaining_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)

    # Status
    is_settled: Mapped[bool] = mapped_column(default=False, nullable=False)
    settlement_date: Mapped[str] = mapped_column(String(50), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)

    # Relationships
    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    def __repr__(self) -> str:
        return f"<Balance {self.document_type}:{self.document_number} - {self.remaining_amount}>"

    def update_balance(self, amount: Decimal, quantity: Decimal) -> None:
        """Update matched amounts and recalculate remaining."""
        self.matched_amount += amount
        self.matched_quantity += quantity
        self.remaining_amount = self.original_amount - self.matched_amount
        self.remaining_quantity = self.original_quantity - self.matched_quantity
        
        if self.remaining_amount <= 0 and self.remaining_quantity <= 0:
            self.is_settled = True

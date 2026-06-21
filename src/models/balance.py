// src/models/balance.py
// src/models/balance.py
"""Balance Ledger model for tracking balances across matched documents."""

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Date,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.purchase_order import PurchaseOrder
    from src.models.invoice import Invoice
    from src.models.delivery_note import DeliveryNote


class BalanceType(str, Enum):
    """Balance type enumeration."""

    PO_OPEN = "po_open"
    PO_INVOICED = "po_invoiced"
    PO_DELIVERED = "po_delivered"
    PO_BILLED = "po_billed"
    INVOICE_OPEN = "invoice_open"
    INVOICE_MATCHED = "invoice_matched"
    INVOICE_PAID = "invoice_paid"
    DELIVERY_OPEN = "delivery_open"
    DELIVERY_RECEIVED = "delivery_received"


class TransactionType(str, Enum):
    """Transaction type for balance ledger."""

    INITIAL = "initial"
    MATCH = "match"
    PARTIAL_MATCH = "partial_match"
    REVERSE = "reverse"
    ADJUSTMENT = "adjustment"
    PAYMENT = "payment"


class BalanceLedger(BaseModel):
    """Balance Ledger model for tracking balances across all document types."""

    __tablename__ = "balance_ledger"

    # Document references
    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
    )
    invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
    )
    delivery_note_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
    )
    match_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matches.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Balance type
    balance_type: Mapped[BalanceType] = mapped_column(
        SQLEnum(BalanceType, name="balance_type"),
        nullable=False,
    )

    # Transaction info
    transaction_type: Mapped[TransactionType] = mapped_column(
        SQLEnum(TransactionType, name="transaction_type"),
        nullable=False,
    )
    transaction_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    reference_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    # Amount tracking
    original_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    previous_balance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    transaction_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    current_balance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    # Line-level tracking
    line_number: Mapped[Optional[int]] = mapped_column(
        nullable=True,
    )
    sku: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    quantity: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 3),
        nullable=True,
    )

    # Metadata
    description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    # Relationships
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        foreign_keys=[purchase_order_id],
        back_populates="balance_entries",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_bl_po_id", "purchase_order_id"),
        Index("ix_bl_invoice_id", "invoice_id"),
        Index("ix_bl_dn_id", "delivery_note_id"),
        Index("ix_bl_match_id", "match_id"),
        Index("ix_bl_balance_type", "balance_type"),
        Index("ix_bl_transaction_date", "transaction_date"),
        Index("ix_bl_sku", "sku"),
    )

    def __repr__(self) -> str:
        return f"<BalanceLedger type={self.balance_type} amount={self.current_balance}>"

    @property
    def is_balanced(self) -> bool:
        """Check if this balance entry represents a balanced state."""
        return self.current_balance == Decimal("0.00")


import uuid

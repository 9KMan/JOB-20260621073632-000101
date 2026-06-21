# models/balance_ledger.py
"""Balance Ledger model for tracking partial matches and balances."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel

if TYPE_CHECKING:
    from models.purchase_order import PurchaseOrder, PurchaseOrderLine
    from models.invoice import Invoice, InvoiceLine
    from models.delivery_note import DeliveryNote, DeliveryNoteLine
    from models.match import Match


class BalanceType(str, Enum):
    """Balance type enumeration."""

    PO_OPEN = "PO_OPEN"
    PO_INVOICED = "PO_INVOICED"
    PO_DELIVERED = "PO_DELIVERED"
    INVOICE_OPEN = "INVOICE_OPEN"
    INVOICE_MATCHED = "INVOICE_MATCHED"
    DN_PENDING = "DN_PENDING"
    DN_RECONCILED = "DN_RECONCILED"


class BalanceLedger(BaseModel):
    """Balance Ledger model for tracking balances across documents."""

    __tablename__ = "balance_ledger"

    balance_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    # Document references
    document_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    document_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # Line reference (optional)
    line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    line_number: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    # Balance tracking
    original_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    current_balance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    variance_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    # Reference to matching
    match_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matches.id"),
        nullable=True,
        index=True,
    )

    # Status
    is_closed: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    closed_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    match: Mapped[Optional["Match"]] = relationship(
        "Match",
        foreign_keys=[match_id],
    )

    __table_args__ = (
        Index("ix_balance_doc", "document_type", "document_id"),
        Index("ix_balance_type_doc", "balance_type", "document_type", "is_closed"),
        Index("ix_balance_match", "match_id"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<BalanceLedger(type={self.balance_type}, doc={self.document_number}, balance={self.current_balance})>"

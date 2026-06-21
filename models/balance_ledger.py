// models/balance_ledger.py
"""BalanceLedger SQLAlchemy model for tracking PO/DN/Invoice balances."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from models.enums import LedgerEntryType

if TYPE_CHECKING:
    from models.purchase_order import PurchaseOrder, PurchaseOrderLine
    from models.invoice import Invoice
    from models.delivery_note import DeliveryNote


class BalanceLedger(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Balance ledger for tracking quantities and amounts across PO, DN, and Invoice.

    This is the authoritative record for remaining balances on purchase orders
    and their associated deliveries and invoices.
    """

    __tablename__ = "balance_ledger"
    __table_args__ = (
        Index("ix_balance_ledger_po_id", "po_id"),
        Index("ix_balance_ledger_po_line_id", "po_line_id"),
        Index("ix_balance_ledger_reference_id", "reference_id"),
        Index("ix_balance_ledger_reference_type", "reference_type"),
    )

    # Reference to PO
    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    po_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Entry Details
    entry_type: Mapped[LedgerEntryType] = mapped_column(String(30), nullable=False)
    reference_type: Mapped[str] = mapped_column(String(30), nullable=False)
    reference_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # Quantities
    quantity_delta: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    quantity_balance_before: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False
    )
    quantity_balance_after: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), nullable=False
    )

    # Amounts
    amount_delta: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    amount_balance_before: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False
    )
    amount_balance_after: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False
    )

    # Metadata
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder"
    )
    purchase_order_line: Mapped[Optional["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine"
    )

    def __repr__(self) -> str:
        return (
            f"<BalanceLedger PO:{self.po_id} "
            f"Type:{self.entry_type} "
            f"QtyDelta:{self.quantity_delta}>"
        )

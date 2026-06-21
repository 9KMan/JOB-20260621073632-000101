// models/balance_ledger.py
"""
BalanceLedger SQLAlchemy model.

The balance ledger tracks running balances for PO lines across
invoices and delivery notes. It provides the foundation for
quantitative matching decisions.
"""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import LineStatus, line_status_enum


class BalanceLedger(Base, UUIDMixin, TimestampMixin):
    """
    Balance Ledger table.
    
    Tracks running balances for each PO line across invoices and DNs.
    This is the quantitative foundation for matching decisions.
    
    Each record represents a balance at a point in time for a specific
    combination of PO line, invoice, and/or delivery note.
    """

    __tablename__ = "balance_ledger"

    # Reference to the Purchase Order line (primary anchor)
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchaseorders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchaseorder_lines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Optional invoice reference
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Optional delivery note reference
    delivery_note_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deliverynotes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    dn_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deliverynote_lines.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Balance quantities
    original_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Original PO line quantity",
    )
    previous_balance: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        doc="Previous running balance before this transaction",
    )
    transaction_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Quantity in this transaction (positive or negative)",
    )
    current_balance: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Running balance after this transaction",
    )

    # Financial amounts
    original_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        doc="Original PO line amount",
    )
    invoiced_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0"),
        doc="Amount applied in this transaction",
    )
    remaining_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        doc="Remaining amount after this transaction",
    )

    # Status
    status: Mapped[LineStatus] = mapped_column(
        line_status_enum,
        nullable=False,
        default=LineStatus.OPEN,
        doc="Balance status",
    )

    # Transaction type
    transaction_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Type: INVOICE, DELIVERY, ADJUSTMENT, CREDIT",
    )

    # Effective date
    effective_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        server_default=func.current_date(),
        doc="Date this balance is effective",
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="balance_ledger_entries",
    )
    invoice: Mapped["Invoice | None"] = relationship(
        "Invoice",
        back_populates="balance_ledger_entries",
    )
    delivery_note: Mapped["DeliveryNote | None"] = relationship(
        "DeliveryNote",
        back_populates="balance_ledger_entries",
    )

    __table_args__ = (
        Index("ix_bl_po_line", "po_line_id"),
        Index("ix_bl_invoice", "invoice_id"),
        Index("ix_bl_dn", "delivery_note_id"),
        Index("ix_bl_po_line_effective", "po_line_id", "effective_date"),
        UniqueConstraint(
            "invoice_line_id",
            "transaction_type",
            name="uq_bl_invoice_transaction",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<BalanceLedger(id={self.id}, "
            f"po_line={self.po_line_id}, "
            f"balance={self.current_balance}, "
            f"type={self.transaction_type})>"
        )

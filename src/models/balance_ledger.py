# src/models/balance_ledger.py
"""Balance Ledger model for AP Automation Core Engine.

Tracks the running balance of purchase order lines, including
quantities ordered, received, invoiced, and paid.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin


class BalanceLedger(TimestampMixin, UUIDMixin, Base):
    """Balance Ledger for tracking PO line balances.

    Provides a real-time view of what's been ordered, received,
    invoiced, and paid for each PO line item.
    """

    __tablename__ = "balance_ledger"

    # Reference to the source document
    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
        doc="Reference to PO line",
    )

    # Document references for audit trail
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
        doc="Invoice that triggered this balance update",
    )
    delivery_note_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="SET NULL"),
        nullable=True,
        doc="Delivery note that triggered this balance update",
    )
    cross_ref_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cross_refs.id", ondelete="SET NULL"),
        nullable=True,
        doc="Cross reference that linked invoice to PO",
    )

    # Transaction type
    transaction_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        doc="Type: order, delivery, invoice, payment, credit, adjustment",
    )
    transaction_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Date of the transaction",
    )
    transaction_reference: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Reference number for the transaction",
    )

    # Quantities (for three-way matching)
    quantity_ordered: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        doc="Original ordered quantity",
    )
    quantity_delivered: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        doc="Quantity delivered",
    )
    quantity_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        doc="Quantity invoiced",
    )
    quantity_paid: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        doc="Quantity paid for",
    )

    # Amounts
    amount_ordered: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        doc="Original ordered amount",
    )
    amount_delivered: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        doc="Delivered amount",
    )
    amount_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        doc="Invoiced amount",
    )
    amount_paid: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        doc="Amount paid",
    )

    # Running balances
    balance_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Remaining balance quantity",
    )
    balance_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Remaining balance amount",
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="active",
        doc="Balance status",
    )
    notes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Additional notes",
    )

    # Relationships
    po_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        foreign_keys=[po_line_id],
    )
    invoice: Mapped["Invoice | None"] = relationship(
        "Invoice",
        foreign_keys=[invoice_id],
    )
    delivery_note: Mapped["DeliveryNote | None"] = relationship(
        "DeliveryNote",
        foreign_keys=[delivery_note_id],
    )
    cross_ref: Mapped["CrossRef | None"] = relationship(
        "CrossRef",
        foreign_keys=[cross_ref_id],
    )

    __table_args__ = (
        Index("ix_balance_ledger_po_line_id", "po_line_id"),
        Index("ix_balance_ledger_invoice_id", "invoice_id"),
        Index("ix_balance_ledger_transaction_type", "transaction_type"),
        Index("ix_balance_ledger_transaction_date", "transaction_date"),
        Index("ix_balance_ledger_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<BalanceLedger for PO Line {self.po_line_id}: Qty {self.balance_quantity}, Amt {self.balance_amount}>"

// models/balance_ledger.py
"""BalanceLedger SQLAlchemy model.

Tracks running balances for purchase order lines after
invoice matching and payments.
"""

import uuid
from decimal import Decimal

from sqlalchemy import (
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin


class BalanceLedger(Base, UUIDMixin, TimestampMixin):
    """Balance ledger entry.

    Maintains a running balance for each PO line showing
    what's been invoiced vs. paid.
    """

    __tablename__ = "balance_ledger"
    __table_args__ = (
        Index("ix_balance_ledger_po_line_id", "po_line_id"),
        Index("ix_balance_ledger_invoice_id", "invoice_id"),
        Index("ix_balance_ledger_created_at", "created_at"),
        UniqueConstraint(
            "po_line_id", "invoice_id", name="uq_po_line_invoice"
        ),
    )

    # Foreign Keys
    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Purchase order line ID",
    )
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Associated invoice ID",
    )
    delivery_note_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Associated delivery note ID",
    )

    # PO Line Reference Information (denormalized for reporting)
    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        doc="Parent purchase order ID",
    )
    po_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Purchase order number (denormalized)",
    )
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Vendor ID (denormalized)",
    )

    # Original PO Values
    po_quantity_ordered: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Original ordered quantity",
    )
    po_quantity_received: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        doc="Total received quantity",
    )
    po_unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="PO unit price",
    )

    # Invoice Values
    invoice_quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        doc="Invoiced quantity for this entry",
    )
    invoice_unit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
        doc="Invoiced unit price",
    )
    invoice_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        doc="Invoice amount for this entry",
    )

    # Running Balances
    balance_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Remaining quantity to invoice",
    )
    balance_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        doc="Remaining amount to pay",
    )

    # Payment Information
    paid_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
        doc="Paid quantity",
    )
    paid_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Paid amount",
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="open",
        doc="Entry status (open, closed, disputed)",
    )
    notes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Notes or comments",
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="balance_ledger_entries",
    )
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="balance_ledger_entries",
    )
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="balance_ledger_entries",
    )

    def __repr__(self) -> str:
        return f"<BalanceLedger PO:{self.po_number} Balance:{self.balance_amount}>"

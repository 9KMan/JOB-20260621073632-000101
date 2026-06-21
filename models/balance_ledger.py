# models/balance_ledger.py
"""BalanceLedger SQLAlchemy model for tracking PO line balances."""

import uuid
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from models.base import BaseModel


class BalanceLedger(BaseModel):
    """
    Balance Ledger model for tracking PO line balances.
    
    This table maintains running balances for each PO line,
    tracking quantities received, invoiced, and paid.
    
    Attributes:
        po_line_id: Reference to PO line
        invoice_id: Reference to invoice (if invoiced)
        delivery_note_id: Reference to DN (if delivered)
        transaction_type: Type of transaction (delivery, invoice, payment)
        quantity_delta: Change in quantity (positive or negative)
        amount_delta: Change in amount (positive or negative)
        running_quantity: Running balance of quantity
        running_amount: Running balance of amount
    """

    __tablename__ = "balance_ledger"

    # References
    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Reference to PO line",
    )
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        doc="Reference to invoice (for invoice/payment transactions)",
    )
    delivery_note_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        doc="Reference to delivery note (for delivery transactions)",
    )

    # Transaction type
    transaction_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        doc="Type: delivery, invoice, payment, adjustment",
    )

    # Quantity tracking
    quantity_delta: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        doc="Change in quantity (positive for additions)",
    )
    running_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        doc="Running balance of quantity",
    )

    # Amount tracking
    amount_delta: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        doc="Change in amount",
    )
    running_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        doc="Running balance of amount",
    )

    # Additional details
    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Transaction description",
    )
    reference_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="External reference number",
    )

    # Relationships
    po_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        back_populates="balance_entries",
    )

    __table_args__ = (
        Index("ix_balance_ledger_po_line_date", "po_line_id", "created_at"),
        Index("ix_balance_ledger_invoice", "invoice_id"),
        Index("ix_balance_ledger_dn", "delivery_note_id"),
        CheckConstraint(
            "transaction_type IN ('delivery', 'invoice', 'payment', 'adjustment', 'credit')",
            name="ck_balance_ledger_transaction_type",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<BalanceLedger(id={self.id}, type={self.transaction_type}, "
            f"qty_delta={self.quantity_delta})>"
        )

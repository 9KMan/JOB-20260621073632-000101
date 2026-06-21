// models/balance_ledger.py
"""BalanceLedger SQLAlchemy model for tracking PO line balances."""

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from models.invoice import InvoiceLine
    from models.purchase_order import PurchaseOrderLine


class BalanceLedger(Base, UUIDMixin, TimestampMixin):
    """Balance Ledger model for tracking running balances per PO line.

    This table maintains an audit trail of quantity and amount movements
    for each purchase order line, tracking:
    - Purchase order quantities
    - Delivery note quantities
    - Invoice quantities
    - Running balances

    Attributes:
        id: UUID primary key
        purchase_order_line_id: Reference to PO line
        invoice_line_id: Reference to invoice line (if applicable)
        transaction_type: Type of transaction (po, dn, invoice, adjustment)
        quantity_change: Change in quantity (positive or negative)
        amount_change: Change in amount (positive or negative)
        balance_quantity: Running balance quantity after this transaction
        balance_amount: Running balance amount after this transaction
        transaction_date: Date of the transaction
        reference_number: External reference number
        notes: Additional notes
    """

    __tablename__ = "balance_ledger"
    __table_args__ = (
        UniqueConstraint(
            "purchase_order_line_id",
            "transaction_type",
            "reference_number",
            name="uq_ledger_transaction",
        ),
        Index("ix_balance_ledger_po_line_id", "purchase_order_line_id"),
        Index("ix_balance_ledger_invoice_line_id", "invoice_line_id"),
        Index("ix_balance_ledger_transaction_date", "transaction_date"),
        Index("ix_balance_ledger_reference_number", "reference_number"),
        {"schema": None},
    )

    # Foreign keys
    purchase_order_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Reference to purchase order line",
    )
    invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Reference to invoice line (for invoice transactions)",
    )

    # Transaction details
    transaction_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        doc="Transaction type: po, dn, invoice, adjustment, credit",
    )
    reference_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="External reference number (PO/DN/Invoice number)",
    )
    transaction_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        doc="Date of the transaction",
    )

    # Quantity tracking
    quantity_change: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=3),
        nullable=False,
        doc="Change in quantity (positive for additions, negative for deductions)",
    )
    balance_quantity: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=3),
        nullable=False,
        doc="Running balance quantity after this transaction",
    )

    # Amount tracking
    amount_change: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
        doc="Change in amount (positive for additions, negative for deductions)",
    )
    balance_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
        doc="Running balance amount after this transaction",
    )

    # Additional details
    notes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Additional notes or description",
    )

    # Relations
    purchase_order_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        back_populates="balance_ledger",
    )
    invoice_line: Mapped["InvoiceLine | None"] = relationship(
        "InvoiceLine",
        back_populates="balance_ledger",
    )

    def __repr__(self) -> str:
        return (
            f"<BalanceLedger(id={self.id}, po_line={self.purchase_order_line_id}, "
            f"type={self.transaction_type}, qty_balance={self.balance_quantity})>"
        )

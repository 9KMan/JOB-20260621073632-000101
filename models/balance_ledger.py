# models/balance_ledger.py
"""BalanceLedger SQLAlchemy model for tracking PO line balances."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from models.invoice import InvoiceLine
    from models.purchase_order import PurchaseOrderLine


class BalanceLedger(Base, UUIDMixin, TimestampMixin):
    """Balance ledger for tracking PO line quantities and values.

    This table maintains a running balance of what has been ordered,
    received, and invoiced for each PO line.
    """

    __tablename__ = "balance_ledger"
    __table_args__ = (
        UniqueConstraint(
            "po_line_id",
            "transaction_type",
            "reference_id",
            name="uq_balance_ledger_transaction",
        ),
        Index("ix_balance_ledger_po_line_id", "po_line_id"),
        Index("ix_balance_ledger_transaction_type", "transaction_type"),
        Index("ix_balance_ledger_reference_id", "reference_id"),
        {"schema": None},
    )

    # References
    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Transaction type
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # Types: ORDER, RECEIVE, INVOICE, CREDIT, PAYMENT, ADJUSTMENT

    # Reference info
    reference_id: Mapped[str] = mapped_column(String(100), nullable=False)
    reference_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # reference_type: PO, DELIVERY_NOTE, INVOICE, CREDIT_MEMO, PAYMENT

    # Quantities
    quantity_before: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=Decimal("0.0000"))
    quantity_change: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=Decimal("0.0000"))
    quantity_after: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=Decimal("0.0000"))

    # Values
    value_before: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    value_change: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    value_after: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))

    # Unit price at transaction time
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=Decimal("0.0000"))

    # Balance type
    balance_type: Mapped[str] = mapped_column(String(20), default="REMAINING", nullable=False)
    # balance_type: REMAINING, RECEIVED, INVOICED, PAID

    # Transaction timestamp
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # User who made the change
    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Notes
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    po_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        back_populates="balance_ledger_entries",
    )
    invoice_line: Mapped["InvoiceLine | None"] = relationship(
        "InvoiceLine",
        back_populates="balance_ledger_entries",
    )

    def __repr__(self) -> str:
        return (
            f"<BalanceLedger {self.transaction_type} - "
            f"Qty: {self.quantity_change} Value: {self.value_change}>"
        )

    @classmethod
    def create_order_entry(
        cls,
        po_line_id: uuid.UUID,
        quantity: Decimal,
        unit_price: Decimal,
        reference_id: str,
        created_by: str | None = None,
        notes: str | None = None,
    ) -> "BalanceLedger":
        """Create a new ORDER entry in the ledger.

        Args:
            po_line_id: Purchase order line ID
            quantity: Quantity ordered
            unit_price: Unit price
            reference_id: PO number
            created_by: User who created
            notes: Optional notes

        Returns:
            BalanceLedger: New ledger entry
        """
        value = quantity * unit_price
        return cls(
            po_line_id=po_line_id,
            transaction_type="ORDER",
            reference_id=reference_id,
            reference_type="PO",
            quantity_before=Decimal("0.0000"),
            quantity_change=quantity,
            quantity_after=quantity,
            value_before=Decimal("0.00"),
            value_change=value,
            value_after=value,
            unit_price=unit_price,
            balance_type="REMAINING",
            transaction_date=datetime.now(timezone.utc),
            created_by=created_by,
            notes=notes,
        )

    @classmethod
    def create_receive_entry(
        cls,
        po_line_id: uuid.UUID,
        quantity: Decimal,
        unit_price: Decimal,
        reference_id: str,
        reference_type: str = "DELIVERY_NOTE",
        created_by: str | None = None,
        notes: str | None = None,
    ) -> "BalanceLedger":
        """Create a RECEIVE entry in the ledger.

        Args:
            po_line_id: Purchase order line ID
            quantity: Quantity received
            unit_price: Unit price
            reference_id: Delivery note number
            reference_type: Type of reference document
            created_by: User who created
            notes: Optional notes

        Returns:
            BalanceLedger: New ledger entry
        """
        value = quantity * unit_price
        return cls(
            po_line_id=po_line_id,
            transaction_type="RECEIVE",
            reference_id=reference_id,
            reference_type=reference_type,
            quantity_before=Decimal("0.0000"),
            quantity_change=quantity,
            quantity_after=quantity,
            value_before=Decimal("0.00"),
            value_change=value,
            value_after=value,
            unit_price=unit_price,
            balance_type="RECEIVED",
            transaction_date=datetime.now(timezone.utc),
            created_by=created_by,
            notes=notes,
        )

    @classmethod
    def create_invoice_entry(
        cls,
        po_line_id: uuid.UUID,
        invoice_line_id: uuid.UUID,
        quantity: Decimal,
        unit_price: Decimal,
        reference_id: str,
        created_by: str | None = None,
        notes: str | None = None,
    ) -> "BalanceLedger":
        """Create an INVOICE entry in the ledger.

        Args:
            po_line_id: Purchase order line ID
            invoice_line_id: Invoice line ID
            quantity: Quantity invoiced
            unit_price: Unit price
            reference_id: Invoice number
            created_by: User who created
            notes: Optional notes

        Returns:
            BalanceLedger: New ledger entry
        """
        value = quantity * unit_price
        return cls(
            po_line_id=po_line_id,
            invoice_line_id=invoice_line_id,
            transaction_type="INVOICE",
            reference_id=reference_id,
            reference_type="INVOICE",
            quantity_before=Decimal("0.0000"),
            quantity_change=quantity,
            quantity_after=quantity,
            value_before=Decimal("0.00"),
            value_change=value,
            value_after=value,
            unit_price=unit_price,
            balance_type="INVOICED",
            transaction_date=datetime.now(timezone.utc),
            created_by=created_by,
            notes=notes,
        )

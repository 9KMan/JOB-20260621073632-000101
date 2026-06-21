# models/balance_ledger.py
"""Balance Ledger model definition for tracking PO/Invoice balances."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Index,
    Numeric,
    String,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from models.invoice import Invoice, InvoiceLine
    from models.purchase_order import PurchaseOrder, PurchaseOrderLine
    from models.delivery_note import DeliveryNote, DeliveryNoteLine


class BalanceLedger(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Balance Ledger for tracking PO line balances.

    This table maintains a running balance of quantities for each PO line,
    tracking how much has been delivered, invoiced, and received.

    Attributes:
        id: UUID primary key
        po_id: Reference to parent PO
        po_line_id: Reference to specific PO line
        transaction_type: Type of transaction (delivery, invoice, adjustment)
        document_type: Type of document (DN, Invoice, Manual)
        document_id: Reference to the document
        document_line_id: Reference to the specific line
        quantity_before: Quantity before this transaction
        quantity_change: Quantity change from this transaction
        quantity_after: Quantity after this transaction
        amount_before: Amount before this transaction
        amount_change: Amount change from this transaction
        amount_after: Amount after this transaction
        notes: Transaction notes
        metadata: Additional flexible fields
    """

    __tablename__ = "balance_ledger"

    # References
    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Transaction details
    transaction_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    document_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    document_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    # Quantity balance
    quantity_before: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.00"),
    )
    quantity_change: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    quantity_after: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )

    # Amount balance
    amount_before: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    amount_change: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    amount_after: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    # Reference numbers
    reference_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Metadata
    metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Tenant
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="balance_entries",
    )
    po_line: Mapped["PurchaseOrderLine"] = relationship(
        "PurchaseOrderLine",
        back_populates="balance_entries",
    )

    __table_args__ = (
        Index("ix_balance_ledger_po_line", "po_line_id"),
        Index("ix_balance_ledger_document", "document_type", "document_id"),
        Index("ix_balance_ledger_tenant", "tenant_id", "po_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<BalanceLedger {self.transaction_type} "
            f"{self.po_line_id}: {self.quantity_change}>"
        )

    @classmethod
    def transaction_types(cls) -> dict[str, str]:
        """Return valid transaction types."""
        return {
            "DELIVERY": "delivery",
            "INVOICE": "invoice",
            "ADJUSTMENT": "adjustment",
            "CREDIT": "credit",
            "RETURN": "return",
            "REVERSAL": "reversal",
        }

    @classmethod
    def document_types(cls) -> dict[str, str]:
        """Return valid document types."""
        return {
            "PURCHASE_ORDER": "purchase_order",
            "DELIVERY_NOTE": "delivery_note",
            "INVOICE": "invoice",
            "CREDIT_NOTE": "credit_note",
            "MANUAL": "manual",
        }

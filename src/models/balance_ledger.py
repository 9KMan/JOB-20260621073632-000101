# src/models/balance_ledger.py
"""Balance Ledger model for tracking PO/Invoice balances."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from models.invoice import Invoice
    from models.purchase_order import PurchaseOrder, PurchaseOrderLine


class BalanceLedger(UUIDMixin, TimestampMixin, Base):
    """
    Balance Ledger tracks the remaining balance on PO lines.
    
    This is a running balance ledger that records:
    - Initial PO line balance
    - Delivery quantities received
    - Invoice quantities invoiced
    - Current remaining balance
    
    Attributes:
        id: Unique identifier (UUID)
        po_id: Purchase order reference
        po_line_id: Specific PO line reference
        invoice_id: Invoice reference (if applicable)
        transaction_type: Type of transaction (po_created, delivery, invoice)
        quantity_change: Change in quantity (+/-)
        amount_change: Change in amount (+/-)
        balance_after: Running balance after transaction
        notes: Transaction notes
    """
    
    __tablename__ = "balance_ledger"
    __table_args__ = (
        Index("ix_balance_ledger_po_id", "po_id"),
        Index("ix_balance_ledger_po_line_id", "po_line_id"),
        Index("ix_balance_ledger_invoice_id", "invoice_id"),
        Index("ix_balance_ledger_transaction_type", "transaction_type"),
        Index("ix_balance_ledger_created_at", "created_at"),
    )
    
    po_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    po_line_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=False,
    )
    invoice_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
    )
    transaction_type: Mapped[str] = mapped_column(
        Enum(
            "po_created",
            "po_updated",
            "delivery_received",
            "invoice_received",
            "credit_note",
            "adjustment",
            name="ledger_transaction_type",
            create_constraint=True,
        ),
        nullable=False,
    )
    quantity_before: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0.0000"),
    )
    quantity_change: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    quantity_after: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
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
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )
    notes: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    reference_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    
    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="balance_ledger",
    )
    invoice: Mapped["Invoice | None"] = relationship(
        "Invoice",
        back_populates="balance_ledger",
    )

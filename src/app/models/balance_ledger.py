// src/app/models/balance_ledger.py
"""Balance Ledger model for tracking partial matches."""
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.models.base import BaseModel

if TYPE_CHECKING:
    from src.app.models.purchase_order import PurchaseOrder
    from src.app.models.invoice import Invoice
    from src.app.models.delivery_note import DeliveryNote


class BalanceLedger(BaseModel):
    """
    Balance Ledger for tracking outstanding balances across PO, Invoice, and Delivery Note.
    
    This supports partial matches and split scenarios:
    - Partial shipments
    - Split invoices
    - Multi-delivery scenarios
    """

    __tablename__ = "balance_ledger"

    # Reference to the source documents
    po_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    delivery_note_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    
    # Document reference numbers for display
    po_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )
    invoice_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )
    dn_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )
    
    # Balance type
    balance_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="OUTSTANDING",
    )
    
    # Amount tracking
    original_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    outstanding_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    
    # Quantity tracking
    original_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    delivered_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
    )
    outstanding_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ACTIVE",
        index=True,
    )
    
    # Resolution
    resolution_date: Mapped[date | None] = mapped_column(
        nullable=True,
    )
    resolution_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Reference to match that created/modified this balance
    match_id: Mapped[uuid.UUID | None] = mapped_column(
        nullable=True,
        index=True,
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder | None"] = relationship(
        foreign_keys=[po_id],
    )
    invoice: Mapped["Invoice | None"] = relationship(
        foreign_keys=[invoice_id],
    )
    delivery_note: Mapped["DeliveryNote | None"] = relationship(
        foreign_keys=[delivery_note_id],
    )

    def __repr__(self) -> str:
        return f"<BalanceLedger {self.balance_type} - {self.outstanding_amount}>"

// src/app/models/balance.py
"""Balance tracking model for partial matches."""
import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.purchase_order import PurchaseOrder
    from app.models.invoice import Invoice
    from app.models.delivery_note import DeliveryNote


class BalanceLedger(BaseModel):
    """Balance ledger for tracking partial matches across documents."""

    __tablename__ = "balance_ledger"

    # Document references
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Balance type: PO_OPEN, PO_INVOICED, PO_DELIVERED, DN_RECEIVED
    balance_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # Document type that created this balance: INVOICE, DELIVERY_NOTE
    source_document_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    source_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    # Original and remaining amounts
    original_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    remaining_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    applied_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Currency
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )

    # Status
    is_settled: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        index=True,
    )
    settled_at: Mapped[uuid | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    # Reference to match if applicable
    match_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="balance_entries",
    )

    # Indexes
    __table_args__ = (
        Index("ix_balance_ledger_po_type", "purchase_order_id", "balance_type"),
        Index("ix_balance_ledger_source", "source_document_type", "source_document_id"),
        Index("ix_balance_ledger_unsettled", "purchase_order_id", "is_settled"),
    )

    def __repr__(self) -> str:
        return f"<BalanceLedger(id={self.id}, balance_type={self.balance_type}, remaining={self.remaining_amount})>"

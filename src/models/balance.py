// src/models/balance.py
"""Balance ledger for tracking partial matches."""
import enum
import uuid
from decimal import Decimal
from datetime import date

from sqlalchemy import String, Numeric, Date, Enum, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class BalanceType(str, enum.Enum):
    """Balance type enumeration."""

    PO_OPEN = "PO_OPEN"
    PO_INVOICED = "PO_INVOICED"
    PO_DELIVERED = "PO_DELIVERED"
    INVOICE_OPEN = "INVOICE_OPEN"
    INVOICE_MATCHED = "INVOICE_MATCHED"
    DELIVERY_OPEN = "DELIVERY_OPEN"
    DELIVERY_MATCHED = "DELIVERY_MATCHED"


class BalanceLedger(Base, TimestampMixin):
    """Balance ledger for tracking partial matches and remaining balances."""

    __tablename__ = "balance_ledger"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    
    # Document references
    po_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    invoice_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
    )
    delivery_note_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
    )
    
    # Balance type
    balance_type: Mapped[BalanceType] = mapped_column(Enum(BalanceType), nullable=False)
    
    # Original amounts
    original_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    original_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    
    # Remaining/billed amounts
    remaining_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    remaining_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    
    # Billed/matched amounts
    billed_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    billed_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), default=Decimal("0"))
    
    # Reference to match
    match_result_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("match_results.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Effective date
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Status
    is_settled: Mapped[bool] = mapped_column(default=False, nullable=False)
    settlement_date: Mapped[date] = mapped_column(Date, nullable=True)

    # Relationships
    po: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        foreign_keys=[po_id],
    )
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        foreign_keys=[invoice_id],
    )
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        foreign_keys=[delivery_note_id],
    )

    __table_args__ = (
        Index("ix_balance_ledger_po", "po_id"),
        Index("ix_balance_ledger_invoice", "invoice_id"),
        Index("ix_balance_ledger_delivery_note", "delivery_note_id"),
        Index("ix_balance_ledger_type_po", "balance_type", "po_id"),
    )

# src/models/balance.py
"""Balance models for tracking partial matches and balances."""

from typing import TYPE_CHECKING, Optional
import uuid
from datetime import date
from decimal import Decimal
import enum

from sqlalchemy import (
    Date,
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.purchase_order import PurchaseOrder
    from src.models.invoice import Invoice
    from src.models.delivery_note import DeliveryNote


class BalanceType(str, enum.Enum):
    """Balance type enumeration."""
    PO_BALANCE = "po_balance"
    INVOICE_BALANCE = "invoice_balance"
    DN_BALANCE = "dn_balance"


class Balance(BaseModel):
    """Balance ledger for tracking partial matches across documents."""

    __tablename__ = "balances"

    # Document references
    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
    )

    invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
    )

    delivery_note_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Balance type
    balance_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    # Line item reference (optional)
    po_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    item_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # Original amounts
    original_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )

    original_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    # Balance amounts
    balanced_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )

    balanced_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    # Remaining balance
    remaining_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )

    remaining_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    # Reference to the match that created this balance
    match_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    # Status
    is_closed: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    closed_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    # Relationships
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="balances",
    )

    invoice: Mapped[Optional["Invoice"]] = relationship(
        "Invoice",
        back_populates="balances",
    )

    delivery_note: Mapped[Optional["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="balances",
    )

    def __repr__(self) -> str:
        return f"<Balance(type={self.balance_type}, item={self.item_code}, remaining={self.remaining_amount})>"

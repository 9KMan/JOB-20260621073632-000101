// src/models/balance.py
"""Balance ledger model for tracking partial matches and balances."""
import enum
import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.delivery_note import DeliveryNote
    from src.models.invoice import Invoice
    from src.models.purchase_order import PurchaseOrder


class BalanceType(str, enum.Enum):
    """Type of balance being tracked."""
    PURCHASE_ORDER = "PURCHASE_ORDER"
    INVOICE = "INVOICE"
    DELIVERY_NOTE = "DELIVERY_NOTE"


class BalanceDirection(str, enum.Enum):
    """Direction of the balance."""
    POSITIVE = "POSITIVE"  # Amount owed/received
    NEGATIVE = "NEGATIVE"  # Overpayment/overdelivery


class Balance(BaseModel):
    """Balance ledger for tracking partial matches across documents."""

    __tablename__ = "balances"

    balance_type: Mapped[BalanceType] = mapped_column(
        Enum(BalanceType),
        nullable=False,
        index=True
    )
    direction: Mapped[BalanceDirection] = mapped_column(
        Enum(BalanceDirection),
        nullable=False
    )
    
    # Original amount
    original_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False
    )
    
    # Balance tracking
    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0"),
        nullable=False
    )
    remaining_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False
    )
    
    # Reference dates
    document_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )
    due_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True
    )
    
    # Status
    is_settled: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        index=True
    )
    settled_at: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True
    )
    
    # References to source documents
    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    delivery_note_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Currency
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False
    )

    # Relationships
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="balances"
    )
    invoice: Mapped[Optional["Invoice"]] = relationship(
        "Invoice",
        back_populates="balances"
    )
    delivery_note: Mapped[Optional["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="balances"
    )

    def __repr__(self) -> str:
        return f"<Balance {self.id}: {self.balance_type.value} - {self.remaining_amount}>"

    def apply_match(self, amount: Decimal) -> Decimal:
        """Apply a match amount and return the new remaining balance."""
        self.matched_amount += amount
        self.remaining_amount = self.original_amount - self.matched_amount
        
        if self.remaining_amount <= Decimal("0.01"):  # Tolerance for rounding
            self.is_settled = True
            self.remaining_amount = Decimal("0")
        
        return self.remaining_amount

    def reverse_match(self, amount: Decimal) -> Decimal:
        """Reverse a previously applied match amount."""
        self.matched_amount -= amount
        self.remaining_amount = self.original_amount - self.matched_amount
        self.is_settled = False
        return self.remaining_amount

    @property
    def balance_percentage(self) -> Decimal:
        """Get percentage of balance remaining."""
        if self.original_amount == 0:
            return Decimal("0")
        return (self.remaining_amount / self.original_amount) * Decimal("100")

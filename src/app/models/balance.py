# src/app/models/balance.py
"""Balance ledger for tracking partial matches and balances."""
import uuid
import decimal
from datetime import datetime
from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import String, DateTime, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.models.base import BaseModel

if TYPE_CHECKING:
    from src.app.models.purchase_order import PurchaseOrder
    from src.app.models.invoice import Invoice
    from src.app.models.delivery_note import DeliveryNote
    from src.app.models.matching import MatchResult


class BalanceType:
    """Type of balance entry."""
    PO_INVOICE = "PO_INVOICE"
    PO_DELIVERY = "PO_DELIVERY"
    INVOICE_DELIVERY = "INVOICE_DELIVERY"
    PAYMENT = "PAYMENT"
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"


class BalanceStatus:
    """Status of balance entry."""
    OPEN = "OPEN"
    PARTIALLY_MATCHED = "PARTIALLY_MATCHED"
    FULLY_MATCHED = "FULLY_MATCHED"
    CLOSED = "CLOSED"
    DISPUTED = "DISPUTED"
    WRITTEN_OFF = "WRITTEN_OFF"


class BalanceLedger(BaseModel):
    """
    Balance ledger for tracking outstanding amounts across documents.
    Supports partial matches, split invoices, and multi-delivery scenarios.
    """
    
    __tablename__ = "balance_ledger"
    
    # Document references
    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    
    invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    
    delivery_note_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    
    match_result_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("match_results.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Balance type
    balance_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    
    status: Mapped[str] = mapped_column(
        String(20),
        default=BalanceStatus.OPEN,
        nullable=False,
        index=True,
    )
    
    # Amount tracking
    original_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    
    matched_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    
    remaining_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    
    # Quantity tracking
    original_quantity: Mapped[Optional[decimal.Decimal]] = mapped_column(
        Numeric(15, 3),
        nullable=True,
    )
    
    matched_quantity: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 3),
        default=decimal.Decimal("0.000"),
        nullable=False,
    )
    
    remaining_quantity: Mapped[Optional[decimal.Decimal]] = mapped_column(
        Numeric(15, 3),
        nullable=True,
    )
    
    # Line reference for line-level tracking
    po_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    
    invoice_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    
    delivery_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Relationships
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="balance_entries",
        foreign_keys=[purchase_order_id],
    )
    
    invoice: Mapped[Optional["Invoice"]] = relationship(
        "Invoice",
        back_populates="balance_entries",
        foreign_keys=[invoice_id],
    )
    
    delivery_note: Mapped[Optional["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="balance_entries",
        foreign_keys=[delivery_note_id],
    )
    
    @property
    def match_percentage(self) -> decimal.Decimal:
        """Calculate the percentage of amount matched."""
        if self.original_amount == 0:
            return decimal.Decimal("0.00")
        return (self.matched_amount / self.original_amount) * 100
    
    @property
    def is_fully_matched(self) -> bool:
        """Check if the balance is fully matched."""
        return self.remaining_amount == 0 and self.status == BalanceStatus.FULLY_MATCHED
    
    @property
    def is_open(self) -> bool:
        """Check if the balance is still open."""
        return self.status == BalanceStatus.OPEN
    
    def update_match(self, amount: decimal.Decimal, quantity: Optional[decimal.Decimal] = None) -> None:
        """
        Update balance with a new match.
        
        Args:
            amount: Amount to add to matched amount
            quantity: Optional quantity to add to matched quantity
        """
        self.matched_amount += amount
        self.remaining_amount = self.original_amount - self.matched_amount
        
        if quantity is not None and self.original_quantity is not None:
            self.matched_quantity += quantity
            self.remaining_quantity = self.original_quantity - self.matched_quantity
        
        # Update status based on remaining amount
        if self.remaining_amount == 0:
            self.status = BalanceStatus.FULLY_MATCHED
        elif self.matched_amount > 0:
            self.status = BalanceStatus.PARTIALLY_MATCHED
    
    def __repr__(self) -> str:
        return f"<BalanceLedger(id={self.id}, type={self.balance_type}, remaining={self.remaining_amount})>"

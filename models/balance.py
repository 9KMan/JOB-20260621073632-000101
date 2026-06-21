// models/balance.py
"""Balance tracking model for partial matches and reconciliation."""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel

if TYPE_CHECKING:
    from models.delivery_note import DeliveryNote
    from models.invoice import Invoice
    from models.purchase_order import PurchaseOrder


class BalanceType(str, Enum):
    """Balance type enumeration."""
    INVOICE_VS_PO = "invoice_vs_po"
    INVOICE_VS_DN = "invoice_vs_dn"
    DN_VS_PO = "dn_vs_po"
    PARTIAL_MATCH = "partial_match"
    OVER_DELIVERY = "over_delivery"
    UNDER_DELIVERY = "under_delivery"
    OVER_INVOICE = "over_invoice"
    UNDER_INVOICE = "under_invoice"


class Balance(BaseModel):
    """
    Balance tracking model for managing partial matches and outstanding balances.
    
    This is the core of Layer 3 - tracking partial shipments, split invoices,
    and multi-delivery scenarios.
    """
    
    __tablename__ = "balances"
    
    # Document references
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
    
    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
    )
    
    # Balance type
    balance_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    
    # Amount tracking
    original_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    
    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    remaining_amount: Mapped[Decimal] = mapped_column(
        nullable=False,
    )
    
    # Quantity tracking
    original_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=True,
    )
    
    matched_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        default=Decimal("0.000"),
        nullable=True,
    )
    
    remaining_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=True,
    )
    
    # Status
    is_resolved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    resolved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    
    resolution_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Reference to the match that created this balance
    match_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    
    # Additional info
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    metadata: Mapped[Optional[dict]] = mapped_column(
        Text,
        nullable=True,
    )  # JSON data
    
    # Relationships
    invoice: Mapped[Optional["Invoice"]] = relationship(
        "Invoice",
        back_populates="balances",
    )
    
    delivery_note: Mapped[Optional["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="balances",
    )
    
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="balances",
    )
    
    def __repr__(self) -> str:
        return f"<Balance {self.balance_type} - {self.remaining_amount}>"
    
    @property
    def match_percentage(self) -> Decimal:
        """Calculate match percentage."""
        if self.original_amount == 0:
            return Decimal("0")
        return (self.matched_amount / self.original_amount) * 100
    
    @property
    def is_overdue(self) -> bool:
        """Check if balance is overdue (implementation depends on business rules)."""
        return not self.is_resolved
    
    def resolve(self, resolved_by: uuid.UUID, notes: str = "") -> None:
        """Mark balance as resolved."""
        self.is_resolved = True
        self.resolved_at = datetime.utcnow()
        self.resolved_by = resolved_by
        self.resolution_notes = notes

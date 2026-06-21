// app/models/balance.py
"""Balance models for tracking partial matches and balances."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.purchase_order import PurchaseOrder
    from app.models.invoice import Invoice
    from app.models.delivery_note import DeliveryNote


class BalanceType(str):
    """Balance type enumeration."""
    PO_BALANCE = "PO_BALANCE"
    INVOICE_BALANCE = "INVOICE_BALANCE"
    DELIVERY_BALANCE = "DELIVERY_BALANCE"


class BalanceStatus(str):
    """Balance status enumeration."""
    OPEN = "OPEN"
    PARTIALLY_APPLIED = "PARTIALLY_APPLIED"
    CLOSED = "CLOSED"
    DISPUTED = "DISPUTED"


class Balance(Base):
    """Balance model for tracking document-level balances."""
    
    __tablename__ = "balances"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    # Balance identification
    balance_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )
    
    balance_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    
    # Reference document
    reference_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    
    reference_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    
    # Amounts
    original_amount: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    
    current_amount: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    
    applied_amount: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default=BalanceStatus.OPEN,
        nullable=False,
        index=True,
    )
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    
    def __repr__(self) -> str:
        return f"<Balance {self.balance_number}>"
    
    def to_dict(self) -> dict:
        """Convert balance to dictionary."""
        return {
            "id": str(self.id),
            "balance_number": self.balance_number,
            "balance_type": self.balance_type,
            "reference_type": self.reference_type,
            "reference_id": str(self.reference_id),
            "original_amount": self.original_amount,
            "current_amount": self.current_amount,
            "applied_amount": self.applied_amount,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class BalanceLedger(Base):
    """Balance Ledger for tracking balance applications across documents."""
    
    __tablename__ = "balance_ledger"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    # Ledger entry identification
    ledger_entry_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )
    
    # Balance reference
    balance_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("balances.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    
    # Document references (for cross-referencing)
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
    
    # Entry type
    entry_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    
    # Amounts
    amount: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    
    running_balance: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    
    # Line-level reference
    line_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    # Status
    is_reversed: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    
    reversed_by_entry_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Metadata
    created_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    source_system: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    
    # Relationships
    balance: Mapped["Balance"] = relationship(
        "Balance",
        back_populates=None,
    )
    
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="balance_entries",
    )
    
    invoice: Mapped[Optional["Invoice"]] = relationship(
        "Invoice",
        back_populates="balance_entries",
    )
    
    delivery_note: Mapped[Optional["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="balance_entries",
    )
    
    def __repr__(self) -> str:
        return f"<BalanceLedger {self.ledger_entry_number}>"
    
    def to_dict(self) -> dict:
        """Convert balance ledger entry to dictionary."""
        return {
            "id": str(self.id),
            "ledger_entry_number": self.ledger_entry_number,
            "balance_id": str(self.balance_id),
            "purchase_order_id": str(self.purchase_order_id) if self.purchase_order_id else None,
            "invoice_id": str(self.invoice_id) if self.invoice_id else None,
            "delivery_note_id": str(self.delivery_note_id) if self.delivery_note_id else None,
            "entry_type": self.entry_type,
            "amount": self.amount,
            "running_balance": self.running_balance,
            "line_reference": self.line_reference,
            "is_reversed": self.is_reversed,
            "reversed_by_entry_id": str(self.reversed_by_entry_id) if self.reversed_by_entry_id else None,
            "notes": self.notes,
            "created_by": self.created_by,
            "source_system": self.source_system,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

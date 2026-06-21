// src/app/models/transaction.py
"""Transaction model for audit trail."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.invoice import Invoice
    from app.models.delivery_note import DeliveryNote
    from app.models.purchase_order import PurchaseOrder


class Transaction(BaseModel):
    """Transaction log for audit trail."""

    __tablename__ = "transactions"

    # Document references
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    delivery_note_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Transaction details
    transaction_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )
    status_from: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    status_to: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    details: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )
    user_agent: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="transactions",
        foreign_keys=[user_id],
    )
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="transactions",
        foreign_keys=[invoice_id],
    )
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="transactions",
        foreign_keys=[delivery_note_id],
    )
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="transactions",
        foreign_keys=[purchase_order_id],
    )

    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, type={self.transaction_type}, action={self.action})>"


# Import relationships at module level to avoid circular imports
from app.models.user import User
from app.models.invoice import Invoice
from app.models.delivery_note import DeliveryNote
from app.models.purchase_order import PurchaseOrder

User.transactions = relationship(
    "Transaction",
    back_populates="user",
    foreign_keys=[Transaction.user_id],
)
Invoice.transactions = relationship(
    "Transaction",
    back_populates="invoice",
    foreign_keys=[Transaction.invoice_id],
)
DeliveryNote.transactions = relationship(
    "Transaction",
    back_populates="transactions",
    foreign_keys=[Transaction.delivery_note_id],
)
PurchaseOrder.transactions = relationship(
    "Transaction",
    back_populates="purchase_order",
    foreign_keys=[Transaction.purchase_order_id],
)

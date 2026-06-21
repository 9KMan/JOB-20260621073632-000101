// src/models/balance.py
"""Balance Ledger model for tracking partial matches."""
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.invoice import Invoice
    from src.models.delivery_note import DeliveryNote
    from src.models.purchase_order import PurchaseOrder


class BalanceLedger(BaseModel):
    """Balance Ledger - tracks remaining balances for partial matches."""
    
    __tablename__ = "balance_ledger"
    
    document_type: Mapped[str] = mapped_column(
        String(length=20),
        nullable=False,
    )
    document_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    document_line_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    purchase_order_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    balance_type: Mapped[str] = mapped_column(
        String(length=20),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(length=3),
        nullable=False,
        default="USD",
    )
    status: Mapped[str] = mapped_column(
        String(length=20),
        nullable=False,
        default="OPEN",
        index=True,
    )
    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
        default=Decimal("0"),
    )
    remaining_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
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
        return f"<BalanceLedger {self.document_type}:{self.document_id} {self.remaining_amount}>"


# Add relationships to parent models
from src.models.invoice import Invoice
from src.models.delivery_note import DeliveryNote
from src.models.purchase_order import PurchaseOrder

Invoice.balance_entries = relationship(
    "BalanceLedger",
    back_populates="invoice",
    foreign_keys="[BalanceLedger.document_id]",
    primaryjoin="and_(BalanceLedger.document_type=='INVOICE', foreign(BalanceLedger.document_id)==Invoice.id)",
)

DeliveryNote.balance_entries = relationship(
    "BalanceLedger",
    back_populates="delivery_note",
    foreign_keys="[BalanceLedger.document_id]",
    primaryjoin="and_(BalanceLedger.document_type=='DELIVERY_NOTE', foreign(BalanceLedger.document_id)==DeliveryNote.id)",
)

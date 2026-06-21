# src/app/models/balances.py
"""Balance Ledger for tracking partial matches."""
import decimal
import uuid
from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DECIMAL, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from src.app.models.purchase_order import PurchaseOrder, PurchaseOrderLine
    from src.app.models.invoice import Invoice, InvoiceLine
    from src.app.models.delivery_note import DeliveryNote, DeliveryNoteLine


class BalanceLedger(Base, UUIDMixin, TimestampMixin):
    """Ledger for tracking balances across partial matches."""
    
    __tablename__ = "balance_ledger"
    __table_args__ = (
        {"schema": "matching"},
    )
    
    # Document type and reference
    document_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    
    # For line-level tracking
    line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    
    # Balance details
    balance_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    quantity: Mapped[decimal.Decimal] = mapped_column(
        Numeric(precision=12, scale=3),
        default=decimal.Decimal("0.000"),
        nullable=False,
    )
    amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    
    # Reference for the transaction that created this balance
    reference_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    reference_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    
    # Status
    is_settled: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        index=True,
    )
    settled_at: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    def __repr__(self) -> str:
        return f"<BalanceLedger(id={self.id}, type={self.document_type}, balance={self.balance_type})>"

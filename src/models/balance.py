// src/models/balance.py
"""Balance ledger models."""
from decimal import Decimal
from enum import Enum
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, String, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel, TimestampMixin


class BalanceType(str, Enum):
    """Balance type."""
    INVOICE = "invoice"
    DELIVERY = "delivery"
    PARTIAL = "partial"


class BalanceLedger(BaseModel, TimestampMixin):
    """Balance ledger for tracking partial matches."""
    
    __tablename__ = "balance_ledger"
    
    invoice_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
    )
    purchase_order_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
    )
    delivery_note_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
    )
    
    balance_type: Mapped[BalanceType] = mapped_column(
        SQLEnum(BalanceType, name="balance_type", create_type=False),
        nullable=False,
    )
    
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
        Numeric(15, 2),
        nullable=False,
    )
    
    original_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    matched_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0.00"),
        nullable=False,
    )
    remaining_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    
    is_settled: Mapped[bool] = mapped_column(default=False, nullable=False)
    
    def __repr__(self) -> str:
        return f"<BalanceLedger {self.id}: {self.balance_type} - {self.remaining_amount}>"

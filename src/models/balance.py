# src/models/balance.py
import uuid
import decimal
from datetime import date
from enum import Enum

from sqlalchemy import String, Numeric, Date, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin, UUIDMixin


class BalanceType(str, Enum):
    """Balance type enumeration."""
    INVOICE_TO_PO = "INVOICE_TO_PO"
    DELIVERY_TO_PO = "DELIVERY_TO_PO"
    INVOICE_TO_DELIVERY = "INVOICE_TO_DELIVERY"


class Balance(Base, UUIDMixin, TimestampMixin):
    """Balance model for tracking partial matches."""
    
    __tablename__ = "balances"
    
    # Balance type
    balance_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    
    # Reference document
    reference_type: Mapped[str] = mapped_column(String(20), nullable=False)  # PO, INVOICE, DN
    reference_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Balances
    original_amount: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    matched_amount: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), default=decimal.Decimal("0.00"), nullable=False)
    remaining_amount: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    
    # Status
    is_settled: Mapped[bool] = mapped_column(default=False, nullable=False)
    settlement_date: Mapped[date] = mapped_column(Date, nullable=True)
    
    # Link to Purchase Order (for reporting)
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="balances", foreign_keys=[purchase_order_id])
    
    def __repr__(self) -> str:
        return f"<Balance {self.balance_type} - Remaining: {self.remaining_amount}>"

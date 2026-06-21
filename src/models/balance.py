// src/models/balance.py
"""Balance tracking models for partial matches."""
import decimal
import uuid
from enum import Enum
from typing import Optional

from sqlalchemy import (
    ForeignKey,
    Index,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel


class BalanceType(str, Enum):
    """Balance type enum."""
    INVOICE = "invoice"
    DELIVERY = "delivery"
    PURCHASE_ORDER = "purchase_order"


class BalanceDirection(str, Enum):
    """Balance direction enum."""
    INVOICE_MINUS_PO = "invoice_minus_po"
    PO_MINUS_INVOICE = "po_minus_invoice"
    PO_MINUS_DELIVERY = "po_minus_delivery"
    DELIVERY_MINUS_PO = "delivery_minus_po"


class Balance(BaseModel):
    """Balance tracking for partial matches and variances."""

    __tablename__ = "balances"

    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
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
    balance_type: Mapped[str] = mapped_column(String(20), nullable=False)
    direction: Mapped[str] = mapped_column(String(30), nullable=False)
    product_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    po_quantity: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 3), default=0, nullable=False)
    matched_quantity: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 3), default=0, nullable=False)
    remaining_quantity: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 3), default=0, nullable=False)
    po_amount: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    matched_amount: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    remaining_amount: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    is_resolved: Mapped[bool] = mapped_column(default=False, nullable=False)
    resolved_at: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="balances",
    )

    __table_args__ = (
        Index("ix_balances_po_unresolved", "purchase_order_id", "is_resolved"),
        Index("ix_balances_product", "product_code", "is_resolved"),
    )

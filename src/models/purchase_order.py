// src/models/purchase_order.py
"""Purchase Order and Purchase Order Line models."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Date,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.supplier import Supplier
    from src.models.match import Match, MatchLine
    from src.models.balance import BalanceLedger


class POStatus(str, Enum):
    """Purchase Order status enumeration."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    PARTIALLY_MATCHED = "partially_matched"
    FULLY_MATCHED = "fully_matched"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class PurchaseOrder(BaseModel):
    """Purchase Order model - the anchor document in 3-way matching."""

    __tablename__ = "purchase_orders"

    po_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[POStatus] = mapped_column(
        SQLEnum(POStatus, name="po_status"),
        default=POStatus.SUBMITTED,
        nullable=False,
    )
    po_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    expected_delivery_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    supplier: Mapped["Supplier"] = relationship(
        "Supplier",
        back_populates="purchase_orders",
        lazy="selectin",
    )
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    matched_invoices: Mapped[list["Match"]] = relationship(
        "Match",
        foreign_keys="Match.purchase_order_id",
        back_populates="purchase_order",
        lazy="selectin",
    )
    matched_delivery_notes: Mapped[list["Match"]] = relationship(
        "Match",
        foreign_keys="Match.delivery_note_id",
        back_populates="delivery_note",
        lazy="selectin",
    )
    balance_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        foreign_keys="BalanceLedger.purchase_order_id",
        back_populates="purchase_order",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_po_supplier_status", "supplier_id", "status"),
        Index("ix_po_date", "po_date"),
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder po_number={self.po_number}>"

    @property
    def total_lines_quantity(self) -> Decimal:
        """Calculate total quantity across all lines."""
        return sum((line.quantity for line in self.lines), Decimal("0"))

    @property
    def total_lines_amount(self) -> Decimal:
        """Calculate total amount across all lines."""
        return sum((line.line_total for line in self.lines), Decimal("0"))


class PurchaseOrderLine(BaseModel):
    """Purchase Order Line item model."""

    __tablename__ = "purchase_order_lines"

    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    line_number: Mapped[int] = mapped_column(
        nullable=False,
    )
    sku: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        default="EA",
        nullable=False,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    delivery_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_pol_purchase_order_line_number", "purchase_order_id", "line_number"),
        Index("ix_pol_sku", "sku"),
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine po_id={self.purchase_order_id} line={self.line_number}>"


import uuid

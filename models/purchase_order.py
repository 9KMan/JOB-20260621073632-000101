# models/purchase_order.py
"""PurchaseOrder and POLine SQLAlchemy models."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import PurchaseOrderStatus, LineStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef


class PurchaseOrder(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Purchase Order model representing PO from ERP."""

    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_purchase_orders_vendor_number", "vendor_number"),
        Index("ix_purchase_orders_po_number", "po_number"),
        Index("ix_purchase_orders_status", "status"),
        Index("ix_purchase_orders_po_date", "po_date"),
        Index("ix_purchase_orders_vendor_po", "vendor_number", "po_number"),
    )

    vendor_number: Mapped[str] = mapped_column(String(50), nullable=False)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    po_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    po_date: Mapped[date] = mapped_column(Date, nullable=False)
    delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    currency_code: Mapped[str] = mapped_column(String(3), default="USD")
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        String(20),
        default=PurchaseOrderStatus.OPEN,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_system: Mapped[str] = mapped_column(String(50), default="erp")
    department_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cost_center: Mapped[str | None] = mapped_column(String(50), nullable=True)

    lines: Mapped[list["POLine"]] = relationship(
        "POLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number} for {self.vendor_name}>"


class POLine(UUIDMixin, TimestampMixin, Base):
    """Purchase Order Line item model."""

    __tablename__ = "po_lines"
    __table_args__ = (
        Index("ix_po_lines_po_id", "po_id"),
        Index("ix_po_lines_line_number", "po_id", "line_number"),
        Index("ix_po_lines_item_number", "item_number"),
    )

    po_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    line_number: Mapped[int] = mapped_column(nullable=False)
    item_number: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), default="EA")
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[LineStatus] = mapped_column(
        String(20),
        default=LineStatus.OPEN,
        nullable=False,
    )
    delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder", back_populates="lines"
    )
    balance_ledger_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="po_line",
        cascade="all, delete-orphan",
    )
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="po_line",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<POLine {self.line_number}: {self.description}>"

    @property
    def open_quantity(self) -> Decimal:
        """Calculate the remaining open quantity."""
        return self.quantity

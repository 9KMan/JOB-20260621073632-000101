// src/models/purchase_order.py
"""Purchase Order and Purchase Order Line models."""
import uuid
import decimal
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    String,
    Date,
    DateTime,
    Numeric,
    Integer,
    ForeignKey,
    Text,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel, SoftDeleteMixin
from src.models.enums import DocumentStatus

if TYPE_CHECKING:
    from src.models.supplier import Supplier
    from src.models.match import MatchLine, BalanceLedger


class PurchaseOrder(BaseModel, SoftDeleteMixin):
    """Purchase Order header."""

    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_po_supplier_status", "supplier_id", "status"),
        Index("ix_po_number", "po_number", unique=True),
    )

    po_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    order_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    expected_delivery_date: Mapped[date] = mapped_column(
        Date,
        nullable=True,
    )
    status: Mapped[DocumentStatus] = mapped_column(
        DocumentStatus.enum,
        default=DocumentStatus.DRAFT,
        nullable=False,
    )
    subtotal: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    tax_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    total_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )
    notes: Mapped[str] = mapped_column(
        Text,
        nullable=True,
    )
    approved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    approved_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    # Relationships
    supplier: Mapped["Supplier"] = relationship(
        "Supplier",
        back_populates="purchase_orders",
    )
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )
    matched_lines: Mapped[list["MatchLine"]] = relationship(
        "MatchLine",
        back_populates="purchase_order_line",
        foreign_keys="MatchLine.po_line_id",
    )
    balance_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="purchase_order",
        foreign_keys="BalanceLedger.po_id",
    )

    def calculate_totals(self) -> None:
        """Calculate subtotal, tax, and total amounts from lines."""
        self.subtotal = sum((line.line_total for line in self.lines), decimal.Decimal("0.00"))
        self.tax_amount = decimal.Decimal("0.00")
        self.total_amount = self.subtotal + self.tax_amount

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number}>"


class PurchaseOrderLine(BaseModel):
    """Purchase Order Line Item."""

    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        Index("ix_pol_po_line", "purchase_order_id", "line_number", unique=True),
    )

    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    product_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    quantity: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        default="EA",
        nullable=False,
    )
    unit_price: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    line_total: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    tax_rate: Mapped[decimal.Decimal] = mapped_column(
        Numeric(5, 4),
        default=decimal.Decimal("0.0000"),
        nullable=False,
    )
    tax_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    expected_delivery_date: Mapped[date] = mapped_column(
        Date,
        nullable=True,
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )
    matched_lines: Mapped[list["MatchLine"]] = relationship(
        "MatchLine",
        back_populates="po_line",
        foreign_keys="MatchLine.po_line_id",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number}: {self.product_code}>"

    def calculate_totals(self) -> None:
        """Calculate line total from quantity and unit price."""
        self.line_total = self.quantity * self.unit_price
        self.tax_amount = self.line_total * self.tax_rate

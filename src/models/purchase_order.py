// src/models/purchase_order.py
"""Purchase Order models."""
import uuid
import decimal
from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String, Integer, Numeric, Date, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin, UUIDMixin, SoftDeleteMixin
from src.models.enums import DocumentStatus

if TYPE_CHECKING:
    from src.models.invoice import InvoiceLine
    from src.models.delivery_note import DeliveryNoteLine
    from src.models.matching import MatchRecord, BalanceLedger


class PurchaseOrder(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Purchase Order model."""
    
    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_po_supplier_number", "supplier_id", "po_number", unique=True),
        Index("ix_po_status", "status"),
        Index("ix_po_created_at", "created_at"),
    )

    po_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )
    supplier_id: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
    )
    supplier_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    supplier_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    order_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    expected_delivery_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    total_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=decimal.Decimal("0.00"),
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )
    status: Mapped[DocumentStatus] = mapped_column(
        String(50),
        default=DocumentStatus.SUBMITTED,
        nullable=False,
        index=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
    )
    metadata: Mapped[Optional[str]] = mapped_column(
        String(2000),
        nullable=True,
    )

    # Relationships
    lines: Mapped[List["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    matched_invoice_lines: Mapped[List["MatchRecord"]] = relationship(
        "MatchRecord",
        back_populates="purchase_order",
        foreign_keys="MatchRecord.purchase_order_id",
    )
    balance_ledger: Mapped[List["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="purchase_order",
        foreign_keys="BalanceLedger.purchase_order_id",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number}>"


class PurchaseOrderLine(Base, UUIDMixin, TimestampMixin):
    """Purchase Order Line Item model."""
    
    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        Index("ix_pol_po_line", "purchase_order_id", "line_number", unique=True),
    )

    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
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
    line_amount: Mapped[decimal.Decimal] = mapped_column(
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
    expected_delivery_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )
    matched_invoice_lines: Mapped[List["MatchRecord"]] = relationship(
        "MatchRecord",
        back_populates="purchase_order_line",
        foreign_keys="MatchRecord.purchase_order_line_id",
    )
    matched_delivery_lines: Mapped[List["MatchRecord"]] = relationship(
        "MatchRecord",
        back_populates="purchase_order_line",
        foreign_keys="MatchRecord.purchase_order_line_dn_id",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number}: {self.product_code}>"

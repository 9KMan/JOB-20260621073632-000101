# models/purchase_order.py
"""PurchaseOrder and PurchaseOrderLine SQLAlchemy models."""

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Numeric,
    String,
    Text,
    Integer,
    Date,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin
from models.enums import PurchaseOrderStatus, LineStatus

if TYPE_CHECKING:
    from models.invoice import InvoiceLine
    from models.delivery_note import DeliveryNoteLine
    from models.balance_ledger import BalanceLedger


class PurchaseOrder(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """
    Top-level purchase order header received from the ERP.

    Attributes
    ----------
    po_number : str
        Unique business key (ERP-generated PO number).
    vendor_id : str
        External vendor identifier.
    vendor_name : str
        Human-readable vendor name.
    order_date : date
        Date the PO was raised.
    delivery_date : date | None
        Requested delivery date.
    currency : str
        ISO 4217 currency code.
    total_amount : Decimal
        Total PO value.
    status : PurchaseOrderStatus
        Current lifecycle status.
    notes : str | None
        Free-text notes.
    """

    __tablename__ = "purchase_orders"

    po_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    vendor_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    order_date: Mapped[uuid.date] = mapped_column(nullable=False)
    delivery_date: Mapped[uuid.date | None] = mapped_column(nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR")
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
        default=Decimal("0"),
    )
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        String(30),
        nullable=False,
        default=PurchaseOrderStatus.DRAFT,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Relationships ────────────────────────────────────────────────────────

    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_purchase_orders_vendor_id", "vendor_id"),
        Index("ix_purchase_orders_status_deleted", "status", "is_deleted"),
    )


class PurchaseOrderLine(Base, UUIDMixin, TimestampMixin):
    """
    Individual line item on a purchase order.

    Attributes
    ----------
    line_number : int
        1-based position within the PO.
    description : str
        Line item description.
    sku : str | None
        Product / SKU identifier.
    quantity : Decimal
        Ordered quantity.
    delivered_quantity : Decimal
        Total quantity delivered (sum of all related delivery note lines).
    invoiced_quantity : Decimal
        Total quantity invoiced (sum of all related invoice lines).
    unit_of_measure : str
        UoM string.
    unit_price : Decimal
        Agreed price per unit.
    line_amount : Decimal
        quantity × unit_price.
    status : LineStatus
        Current matching status.
    delivery_note_line_id : uuid.UUID | None
        Foreign key to the anchored DeliveryNoteLine (set by Layer 2 cascade).
    """

    __tablename__ = "purchase_order_lines"

    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
        default=Decimal("0"),
    )
    delivered_quantity: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
        default=Decimal("0"),
    )
    invoiced_quantity: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
        default=Decimal("0"),
    )
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=False, default="PCS")
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
        default=Decimal("0"),
    )
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
        default=Decimal("0"),
    )
    status: Mapped[LineStatus] = mapped_column(
        String(30),
        nullable=False,
        default=LineStatus.OPEN,
        index=True,
    )
    delivery_note_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Relationships ────────────────────────────────────────────────────────

    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder", back_populates="lines"
    )
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="po_line",
        foreign_keys="InvoiceLine.po_line_id",
    )
    delivery_note_line: Mapped["DeliveryNoteLine | None"] = relationship(
        "DeliveryNoteLine",
        back_populates="po_line",
        foreign_keys=[delivery_note_line_id],
    )
    balance_ledger_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="po_line",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("purchase_order_id", "line_number", name="uq_po_line_number"),
        Index("ix_po_lines_sku", "sku"),
        Index("ix_po_lines_po_id", "purchase_order_id"),
    )

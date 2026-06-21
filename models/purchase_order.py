# models/purchase_order.py
"""Purchase Order model definition."""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from models.enums import PurchaseOrderStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef
    from models.delivery_note import DeliveryNote
    from models.invoice import InvoiceLine


class PurchaseOrder(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Purchase Order model representing a PO from the ERP system."""

    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_po_vendor_number", "vendor_number"),
        Index("ix_po_po_number", "po_number"),
        Index("ix_po_status", "status"),
        Index("ix_po_order_date", "order_date"),
    )

    # Header fields
    vendor_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    po_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        Enum(PurchaseOrderStatus),
        default=PurchaseOrderStatus.DRAFT,
        nullable=False,
        index=True,
    )

    # Amount fields
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")

    # Additional fields
    payment_terms: Mapped[str | None] = mapped_column(String(100), nullable=True)
    shipping_terms: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # ERP reference
    erp_id: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)

    # Relationships
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )
    delivery_notes: Mapped[list["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="purchase_order",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number} - {self.vendor_number}>"


class PurchaseOrderLine(Base, UUIDMixin, TimestampMixin):
    """Purchase Order Line Item model."""

    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        Index("ix_pol_po_id", "purchase_order_id"),
        Index("ix_pol_line_number", "line_number"),
        Index("ix_pol_item_number", "item_number"),
    )

    purchase_order_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )

    line_number: Mapped[str] = mapped_column(String(50), nullable=False)
    item_number: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    ordered_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    received_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=Decimal("0"))
    invoiced_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=Decimal("0"))
    unit_of_measure: Mapped[str | None] = mapped_column(String(20), nullable=True)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    tax_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    # Calculated fields
    remaining_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=Decimal("0"),
    )
    remaining_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0"),
    )

    # Status
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="purchase_order_line",
    )
    delivery_note_lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="purchase_order_line",
    )
    balance_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="purchase_order_line",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number}: {self.description[:30]}>"

    def update_remaining(self) -> None:
        """Update remaining quantity and amount based on received and invoiced."""
        self.remaining_quantity = self.ordered_quantity - self.received_quantity - self.invoiced_quantity
        self.remaining_amount = self.remaining_quantity * self.unit_price
        if self.remaining_quantity <= 0:
            self.is_closed = True

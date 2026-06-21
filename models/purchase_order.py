# models/purchase_order.py
"""PurchaseOrder and POLine SQLAlchemy models."""

import uuid
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import POStatusType


class PurchaseOrder(Base, UUIDMixin, TimestampMixin):
    """Purchase Order header record from ERP."""

    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_purchase_orders_vendor_code", "vendor_code"),
        Index("ix_purchase_orders_po_number", "po_number", unique=True),
        Index("ix_purchase_orders_status", "status"),
        Index("ix_purchase_orders_created_at", "created_at"),
        UniqueConstraint("vendor_code", "po_number", name="uq_vendor_po"),
    )

    po_number: Mapped[str] = mapped_column(String(50), nullable=False)
    vendor_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vendor_tax_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    # Amounts
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Dates
    po_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    expected_delivery_date: Mapped[Date | None] = mapped_column(Date, nullable=True)

    status: Mapped[POStatusType] = mapped_column(
        POStatusType,
        default=POStatusType.SENT,
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    attachment_urls: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(500)), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # ── Relationships ─────────────────────────────────────────────────────────

    lines: Mapped[list["POLine"]] = relationship(
        "POLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    matched_invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        foreign_keys="Invoice.matched_po_id",
        back_populates="matched_po",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number} vendor={self.vendor_code} status={self.status}>"


class POLine(Base, UUIDMixin, TimestampMixin):
    """Line item on a Purchase Order."""

    __tablename__ = "po_lines"
    __table_args__ = (
        Index("ix_po_lines_po_id", "po_id"),
        Index("ix_po_lines_line_number", "line_number"),
    )

    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )

    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Quantities
    quantity_ordered: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    quantity_received: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), default=Decimal("0")
    )
    quantity_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), default=Decimal("0")
    )

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Matched Invoice Lines
    matched_invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        foreign_keys="InvoiceLine.po_line_id",
        back_populates="po_line",
    )

    # Balance computed at service layer
    @property
    def quantity_balance(self) -> Decimal:
        """Remaining quantity not yet invoiced."""
        return self.quantity_ordered - self.quantity_invoiced

    def __repr__(self) -> str:
        return f"<POLine {self.line_number} qty_ord={self.quantity_ordered}>"

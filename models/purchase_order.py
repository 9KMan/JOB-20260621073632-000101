# models/purchase_order.py
"""PurchaseOrder and PurchaseOrderLine SQLAlchemy models."""

import uuid
from decimal import Decimal
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PurchaseOrder(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Purchase order header model."""

    __tablename__ = "purchase_orders"

    # Vendor Information
    vendor_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    vendor_address: Mapped[str | None] = mapped_column(Text, nullable=True)

    # PO Details
    po_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )
    po_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Financial
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    tax_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        default="approved",
        nullable=False,
        index=True,
    )

    # Approval
    approved_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Soft Delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice",
        back_populates="purchase_order",
        lazy="selectin",
    )
    delivery_notes: Mapped[list["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="purchase_order",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_purchase_orders_vendor_date", "vendor_id", "po_date"),
    )


class PurchaseOrderLine(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Purchase order line item model."""

    __tablename__ = "purchase_order_lines"

    # Parent
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Line Details
    line_number: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)

    # Product/Service Reference
    product_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    product_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Quantities
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    unit_of_measure: Mapped[str | None] = mapped_column(String(20), nullable=True)
    received_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        default=Decimal("0"),
        nullable=False,
    )
    invoiced_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        default=Decimal("0"),
        nullable=False,
    )

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False,
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )

    __table_args__ = (
        Index("ix_po_lines_po_line", "purchase_order_id", "line_number"),
        Index("ix_po_lines_product", "product_code"),
    )

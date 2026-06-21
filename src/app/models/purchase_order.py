// src/app/models/purchase_order.py
"""Purchase Order models."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    String,
    Numeric,
    Date,
    DateTime,
    Text,
    ForeignKey,
    Enum as SQLEnum,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.match import Match

PO_STATUS = Enum("PO_STATUS", ["DRAFT", "SENT", "CONFIRMED", "PARTIAL", "CLOSED", "CANCELLED"])


class PurchaseOrder(Base, UUIDMixin, TimestampMixin):
    """Purchase Order model."""

    __tablename__ = "purchase_orders"

    po_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    supplier_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    supplier_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[PO_STATUS] = mapped_column(
        SQLEnum(PO_STATUS, name="po_status"),
        default=PO_STATUS.DRAFT,
        nullable=False,
    )
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_po_supplier_status", "supplier_id", "status"),
        Index("ix_po_order_date", "order_date"),
    )


class PurchaseOrderLine(Base, UUIDMixin, TimestampMixin):
    """Purchase Order Line Item model."""

    __tablename__ = "purchase_order_lines"

    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(nullable=False)
    product_code: Mapped[str] = mapped_column(String(100), nullable=False)
    product_description: Mapped[str] = mapped_column(Text, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), default="EA")
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    expected_delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )

    __table_args__ = (
        Index("ix_pol_po_id", "purchase_order_id"),
        Index("ix_pol_product_code", "product_code"),
    )

"""PurchaseOrder and PurchaseOrderLine ORM models."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from models.enums import DocumentStatus


class PurchaseOrder(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Header-level purchase order sourced from ERP."""

    __tablename__ = "purchase_orders"

    po_number: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True
    )
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    order_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    expected_delivery: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"))
    status: Mapped[DocumentStatus] = mapped_column(
        String(32), nullable=False, default=DocumentStatus.INGESTED, index=True
    )
    buyer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    lines: Mapped[List["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ux_purchase_orders_vendor_po_no", "vendor_id", "po_number", unique=True),
    )


class PurchaseOrderLine(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Line item on a purchase order; these are the source of truth for matching."""

    __tablename__ = "purchase_order_lines"

    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(nullable=False)
    sku: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    description: Mapped[str] = mapped_column(String(1024), nullable=False)
    ordered_qty: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    received_qty: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"))
    invoiced_qty: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    uom: Mapped[str] = mapped_column(String(16), nullable=False, default="EA")
    gl_account: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    cost_center: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    purchase_order: Mapped[PurchaseOrder] = relationship(
        "PurchaseOrder", back_populates="lines"
    )

    __table_args__ = (
        Index(
            "ux_purchase_order_lines_po_line_no",
            "purchase_order_id",
            "line_number",
            unique=True,
        ),
        Index("ix_purchase_order_lines_sku", "sku"),
    )

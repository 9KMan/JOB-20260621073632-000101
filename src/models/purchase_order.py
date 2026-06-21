// src/models/purchase_order.py
"""Purchase Order models."""
import decimal
import uuid
from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.models.base import BaseModel


class POStatus(str, Enum):
    """Purchase Order status enum."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    PARTIALLY_MATCHED = "partially_matched"
    FULLY_MATCHED = "fully_matched"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class PurchaseOrder(BaseModel):
    """Purchase Order model."""

    __tablename__ = "purchase_orders"

    po_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    supplier_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    subtotal: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    tax_amount: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    total_amount: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=POStatus.DRAFT.value, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    lines: Mapped[List["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )
    invoices: Mapped[List["Invoice"]] = relationship(
        "Invoice",
        back_populates="purchase_order",
    )
    delivery_notes: Mapped[List["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="purchase_order",
    )
    matches: Mapped[List["Match"]] = relationship(
        "Match",
        back_populates="purchase_order",
    )
    balances: Mapped[List["Balance"]] = relationship(
        "Balance",
        back_populates="purchase_order",
    )

    __table_args__ = (
        Index("ix_purchase_orders_supplier_status", "supplier_id", "status"),
    )


class PurchaseOrderLine(BaseModel):
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
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), default="EA", nullable=False)
    unit_price: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_total: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_rate: Mapped[decimal.Decimal] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    tax_amount: Mapped[decimal.Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    expected_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )

    __table_args__ = (
        Index("ix_purchase_order_lines_po_id_line", "purchase_order_id", "line_number", unique=True),
    )

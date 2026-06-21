// app/models/purchase_order.py
"""Purchase Order and POLine SQLAlchemy models."""

import uuid
from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from app.models.enums import POStatus


class PurchaseOrder(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """
    Purchase Order header model.
    
    Represents a PO created in the ERP system.
    """

    __tablename__ = "purchase_orders"

    # Vendor information
    vendor_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    vendor_tax_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # PO details
    po_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    po_date: Mapped[date] = mapped_column(Date, nullable=False)
    delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Financial amounts
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")

    # Status
    status: Mapped[POStatus] = mapped_column(
        String(20),
        nullable=False,
        default=POStatus.ACTIVE,
        index=True,
    )

    # Reference
    requisition_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    project_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    cost_center: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Metadata
    payment_terms: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_system: Mapped[str] = mapped_column(String(50), nullable=False, default="erp")

    # Delivery tracking
    is_fully_delivered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_fully_invoiced: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    lines: Mapped[List["POLine"]] = relationship(
        "POLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Table indexes
    __table_args__ = (
        Index("ix_pos_vendor_date", "vendor_id", "po_date"),
        Index("ix_pos_status_date", "status", "po_date"),
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder(id={self.id}, number={self.po_number}, vendor={self.vendor_id})>"


class POLine(Base, UUIDMixin, TimestampMixin):
    """
    Purchase Order Line item model.
    
    Represents individual line items on a PO.
    """

    __tablename__ = "po_lines"

    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Line details
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)

    # Product/Service info
    product_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    product_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=False, default="EA")

    # Quantities
    quantity_ordered: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    quantity_delivered: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
    )
    quantity_invoiced: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
    )

    # Pricing
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Tax
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=Decimal("0.0000"))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))

    # Delivery tracking
    delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_fully_delivered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_fully_invoiced: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationship
    purchase_order: Mapped["PurchaseOrder"] = relationship("PurchaseOrder", back_populates="lines")

    __table_args__ = (
        Index("ix_po_lines_po_line", "po_id", "line_number"),
        Index("ix_po_lines_product", "product_code"),
    )

    def __repr__(self) -> str:
        return f"<POLine(id={self.id}, line={self.line_number}, product={self.product_code})>"

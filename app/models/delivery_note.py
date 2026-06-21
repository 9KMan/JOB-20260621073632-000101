// app/models/delivery_note.py
"""Delivery Note and DNLine SQLAlchemy models."""

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
from app.models.enums import DNStatus


class DeliveryNote(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """
    Delivery Note header model.
    
    Represents goods received or delivered from vendors.
    """

    __tablename__ = "delivery_notes"

    # Vendor information
    vendor_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    vendor_tax_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # DN details
    dn_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    dn_date: Mapped[date] = mapped_column(Date, nullable=False)
    receipt_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Reference
    po_ref: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    matched_po_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Financial amounts
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")

    # Status
    status: Mapped[DNStatus] = mapped_column(
        String(20),
        nullable=False,
        default=DNStatus.RECEIVED,
        index=True,
    )

    # Metadata
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_system: Mapped[str] = mapped_column(String(50), nullable=False, default="erp")

    # Relationships
    lines: Mapped[List["DNLine"]] = relationship(
        "DNLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    matched_po: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        foreign_keys=[matched_po_id],
        backref="matched_delivery_notes",
    )

    # Table indexes
    __table_args__ = (
        Index("ix_dns_vendor_date", "vendor_id", "dn_date"),
        Index("ix_dns_status_date", "status", "dn_date"),
        Index("ix_dns_po_ref", "po_ref"),
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote(id={self.id}, number={self.dn_number}, vendor={self.vendor_id})>"


class DNLine(Base, UUIDMixin, TimestampMixin):
    """
    Delivery Note Line item model.
    
    Represents individual line items on a delivery note.
    """

    __tablename__ = "dn_lines"

    dn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
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
    quantity_delivered: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    quantity_received: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False,
        default=Decimal("0.000"),
    )

    # Pricing (for matching)
    unit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 4), nullable=True)
    line_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Reference
    po_line_ref: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    matched_po_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("po_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Delivery tracking
    delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_accepted: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationship
    delivery_note: Mapped["DeliveryNote"] = relationship("DeliveryNote", back_populates="lines")
    matched_po_line: Mapped[Optional["POLine"]] = relationship(
        "POLine",
        foreign_keys=[matched_po_line_id],
        backref="matched_dn_lines",
    )

    __table_args__ = (
        Index("ix_dn_lines_dn_line", "dn_id", "line_number"),
        Index("ix_dn_lines_product", "product_code"),
        Index("ix_dn_lines_po_ref", "po_line_ref"),
    )

    def __repr__(self) -> str:
        return f"<DNLine(id={self.id}, line={self.line_number}, product={self.product_code})>"


# Import for relationship resolution
from app.models.purchase_order import PurchaseOrder, POLine

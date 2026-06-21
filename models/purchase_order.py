# models/purchase_order.py
"""Purchase Order model."""

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKey

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef
    from models.delivery_note import DeliveryNoteLine
    from models.invoice import InvoiceLine


class PurchaseOrder(Base, UUIDPrimaryKey, TimestampMixin, SoftDeleteMixin):
    """Purchase order header model."""

    __tablename__ = "purchase_orders"

    po_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    vendor_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    po_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False, index=True)

    # ERP reference
    erp_po_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    source_system: Mapped[str] = mapped_column(String(50), default="erp", nullable=False)

    # Additional metadata
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    lines: Mapped[list["POLine"]] = relationship(
        "POLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_po_vendor_date", "vendor_code", "po_date"),
        {"schema": None},
    )


class POLine(Base, UUIDPrimaryKey):
    """Purchase order line item model."""

    __tablename__ = "po_lines"

    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    line_number: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), default="EA", nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tax_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)

    # Delivery tracking
    delivered_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), default=Decimal("0.0000"), nullable=False
    )
    invoiced_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4), default=Decimal("0.0000"), nullable=False
    )

    # Status
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)

    # Additional data
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship("PurchaseOrder", back_populates="lines")
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine", back_populates="po_line"
    )
    delivery_lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine", back_populates="po_line"
    )
    balance_ledger: Mapped["BalanceLedger | None"] = relationship(
        "BalanceLedger", back_populates="po_line", uselist=False
    )
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        foreign_keys="CrossRef.po_line_id",
        back_populates="po_line_record",
    )

    __table_args__ = (
        UniqueConstraint("po_id", "line_number", name="uq_po_line_number"),
        Index("ix_po_lines_status", "status"),
    )

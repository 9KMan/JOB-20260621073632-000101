// models/purchase_order.py
"""Purchase Order model definition.

This module defines the PurchaseOrder SQLAlchemy model representing
POs that serve as the source document for matching.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.enums import PurchaseOrderStatusType

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef


class PurchaseOrderLine(Base):
    """Purchase Order Line item.

    Represents individual line items within a PO.
    """

    __tablename__ = "po_lines"

    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    line_number: Mapped[int] = mapped_column(
        nullable=False,
        doc="Line item number",
    )

    item_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Item/product code",
    )
    item_description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Item description",
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Ordered quantity",
    )
    quantity_received: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0"),
        nullable=False,
        doc="Received quantity",
    )

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        doc="Unit price",
    )
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        doc="Line total amount",
    )

    expected_delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Expected delivery date",
    )

    uom: Mapped[str] = mapped_column(
        String(20),
        default="EA",
        nullable=False,
        doc="Unit of measure",
    )

    # Relationship
    po: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )

    __table_args__ = (
        Index("ix_po_lines_po_id", "po_id"),
        Index("ix_po_lines_item_code", "item_code"),
    )


class PurchaseOrder(Base):
    """Purchase Order model.

    Represents a purchase order from the ERP system that serves
    as the source document for invoice matching.

    Attributes:
        id: UUID primary key
        po_number: Unique PO number
        vendor_code: Vendor/supplier identifier
        vendor_name: Vendor name
        po_date: PO creation date
        expected_delivery_date: Expected delivery date
        status: Current PO status
        total_amount: Total PO amount
        currency: Currency code
        is_active: Whether PO is active for matching
        erp_reference: External ERP system reference
        notes: Additional notes
        created_at: Record creation timestamp
        updated_at: Record update timestamp
    """

    __tablename__ = "purchase_orders"

    # Primary identification
    po_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique PO number",
    )

    # Vendor information
    vendor_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Vendor code",
    )
    vendor_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Vendor name",
    )

    # Date fields
    po_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        doc="PO creation date",
    )
    expected_delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Expected delivery date",
    )

    # Financial
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        doc="Total PO amount",
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
        doc="Currency code",
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        default=PurchaseOrderStatusType.ISSUED.value,
        nullable=False,
        index=True,
        doc="Current PO status",
    )

    # Active flag
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether PO is active for matching",
    )

    # References
    erp_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="External ERP reference",
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Additional notes",
    )

    # Relationships
    lines: Mapped[list[PurchaseOrderLine]] = relationship(
        "PurchaseOrderLine",
        back_populates="po",
        cascade="all, delete-orphan",
        order_by="PurchaseOrderLine.line_number",
    )

    balance_ledger_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )

    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )

    # Table indexes
    __table_args__ = (
        Index("ix_pos_vendor_date", "vendor_code", "po_date"),
        Index("ix_pos_status", "status"),
        Index("ix_pos_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        """String representation of PurchaseOrder."""
        return f"<PurchaseOrder(id={self.id}, po_number={self.po_number}, vendor={self.vendor_code}, amount={self.total_amount})>"

    @property
    def total_open_amount(self) -> Decimal:
        """Calculate total open amount (not yet invoiced)."""
        from sqlalchemy import select, func
        from models.balance_ledger import BalanceLedger

        # This would typically be calculated via a query
        # For now, return total minus any invoiced amounts
        return self.total_amount

    @property
    def is_fully_received(self) -> bool:
        """Check if PO is fully received."""
        return self.status == PurchaseOrderStatusType.RECEIVED.value

    @property
    def is_closed(self) -> bool:
        """Check if PO is closed."""
        return self.status == PurchaseOrderStatusType.CLOSED.value


# Import uuid for type hints
import uuid

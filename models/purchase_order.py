// models/purchase_order.py
"""Purchase Order model for the AP Automation Engine."""

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, CustomMixin, SoftDeleteMixin
from models.enums import DocumentStatus, MatchStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef
    from models.delivery_note import DeliveryNote
    from models.invoice import Invoice, InvoiceLine


class PurchaseOrder(Base, CustomMixin, SoftDeleteMixin):
    """Purchase Order model.

    Attributes:
        po_number: Unique PO number.
        vendor_id: External vendor identifier.
        vendor_name: Vendor name for display.
        po_date: PO creation date.
        delivery_date: Expected delivery date.
        status: Current document status.
        match_status: Current matching status.
        subtotal: Pre-tax PO amount.
        tax_amount: Tax amount.
        total_amount: Total PO amount.
        currency: ISO currency code.
        payment_terms: Payment terms description.
        ship_to: Shipping address.
        bill_to: Billing address.
        notes: Additional notes.
        is_blanket: Whether this is a blanket PO.
        blanket_release_number: For blanket POs, the release number.
    """

    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_po_vendor_id", "vendor_id"),
        Index("ix_po_status", "status"),
        Index("ix_po_match_status", "match_status"),
        Index("ix_po_po_date", "po_date"),
        Index("ix_po_created_at", "created_at"),
        {"schema": None},
    )

    # Core PO fields
    po_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    vendor_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    po_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Status fields
    status: Mapped[DocumentStatus] = mapped_column(
        String(20),
        default=DocumentStatus.DRAFT,
        nullable=False,
    )
    match_status: Mapped[MatchStatus] = mapped_column(
        String(20),
        default=MatchStatus.PENDING,
        nullable=False,
    )

    # Financial fields
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
        index=True,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )

    # Additional fields
    payment_terms: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    ship_to: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    bill_to: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    is_blanket: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    blanket_release_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # Relationships
    po_lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )
    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="purchase_order",
        foreign_keys="CrossRef.purchase_order_id",
        cascade="all, delete-orphan",
    )
    delivery_notes: Mapped[list["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="purchase_order",
        foreign_keys="DeliveryNote.po_id",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number} - {self.total_amount} {self.currency}>"


class PurchaseOrderLine(Base, CustomMixin):
    """Purchase Order line item model.

    Attributes:
        po_id: Parent PO ID.
        line_number: Line item number.
        description: Line description.
        quantity: Ordered quantity.
        received_quantity: Quantity received so far.
        invoiced_quantity: Quantity invoiced so far.
        unit_price: Price per unit.
        amount: Total line amount.
        tax_code: Tax classification code.
        expected_delivery_date: Expected delivery for this line.
        line_status: Current status of the line.
    """

    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        Index("ix_po_line_po_id", "po_id"),
        {"schema": None},
    )

    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    received_quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    invoiced_quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    tax_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    expected_delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="po_lines",
    )
    invoice_lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="po_line",
    )

    @property
    def remaining_quantity(self) -> Decimal:
        """Calculate remaining uninvoiced quantity."""
        return self.quantity - self.invoiced_quantity

    @property
    def is_fully_invoiced(self) -> bool:
        """Check if line is fully invoiced."""
        return self.invoiced_quantity >= self.quantity

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number} - {self.amount}>"

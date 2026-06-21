# models/invoice.py
"""Invoice and InvoiceLine SQLAlchemy models."""

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Numeric,
    String,
    Text,
    Integer,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin
from models.enums import InvoiceStatus, LineStatus

if TYPE_CHECKING:
    from models.purchase_order import PurchaseOrderLine
    from models.balance_ledger import BalanceLedger


class Invoice(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """
    Top-level invoice header.

    Attributes
    ----------
    invoice_number : str
        Unique business key for the invoice ( ERP-generated).
    vendor_id : str
        External vendor identifier.
    vendor_name : str
        Human-readable vendor name.
    invoice_date : date
        Date printed on the invoice.
    due_date : date
        Payment due date.
    subtotal : Decimal
        Sum of all lines before tax.
    tax_amount : Decimal
        Tax amount.
    total_amount : Decimal
        Total amount payable (subtotal + tax).
    currency : str
        ISO 4217 currency code (e.g. EUR, USD).
    status : InvoiceStatus
        Current lifecycle status.
    notes : str | None
        Free-text notes or internal comments.
    """

    __tablename__ = "invoices"

    invoice_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    vendor_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    invoice_date: Mapped[uuid.date] = mapped_column(nullable=False)
    due_date: Mapped[uuid.date | None] = mapped_column(nullable=True)
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
        default=Decimal("0"),
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
        default=Decimal("0"),
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
        default=Decimal("0"),
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR")
    status: Mapped[InvoiceStatus] = mapped_column(
        String(30),
        nullable=False,
        default=InvoiceStatus.DRAFT,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Relationships ────────────────────────────────────────────────────────

    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_invoices_vendor_date", "vendor_id", "invoice_date"),
        Index("ix_invoices_status_deleted", "status", "is_deleted"),
    )


class InvoiceLine(Base, UUIDMixin, TimestampMixin):
    """
    Individual line item on an invoice.

    Attributes
    ----------
    line_number : int
        1-based position of this line within the invoice.
    description : str
        Line item description.
    sku : str | None
        Product / SKU identifier.
    quantity : Decimal
        Billed quantity.
    unit_of_measure : str
        UoM string (e.g. PCS, KG).
    unit_price : Decimal
        Price per unit.
    line_amount : Decimal
        quantity × unit_price.
    po_line_id : uuid.UUID | None
        Foreign key to the anchored PurchaseOrderLine (set by Layer 1).
    status : LineStatus
        Current matching status of this line.
    """

    __tablename__ = "invoice_lines"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
        default=Decimal("0"),
    )
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=False, default="PCS")
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
        default=Decimal("0"),
    )
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
        default=Decimal("0"),
    )
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[LineStatus] = mapped_column(
        String(30),
        nullable=False,
        default=LineStatus.OPEN,
        index=True,
    )

    # ── Relationships ────────────────────────────────────────────────────────

    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="lines")
    po_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        back_populates="invoice_lines",
        foreign_keys=[po_line_id],
    )
    balance_ledger_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="invoice_line",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("invoice_id", "line_number", name="uq_invoice_line_number"),
        Index("ix_invoice_lines_po_line_id", "po_line_id"),
    )

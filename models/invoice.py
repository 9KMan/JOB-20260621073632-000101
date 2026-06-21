// models/invoice.py
"""Invoice and InvoiceLine SQLAlchemy models.

Invoices are received from vendors and matched against purchase orders
and delivery notes for approval.
"""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.enums import InvoiceStatus


class Invoice(Base):
    """Invoice header model.

    Represents a vendor invoice received for processing.
    """

    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_vendor_code", "vendor_code"),
        Index("ix_invoices_invoice_number", "invoice_number", unique=True),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_invoice_date", "invoice_date"),
        Index("ix_invoices_created_at", "created_at"),
    )

    # External references
    vendor_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    invoice_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Financial fields
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False
    )
    tax_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD")

    # Status and matching
    status: Mapped[InvoiceStatus] = mapped_column(
        InvoiceStatus,
        default=InvoiceStatus.DRAFT,
        nullable=False,
    )
    matched_po_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    matched_dn_ids: Mapped[list[UUID] | None] = mapped_column(
        ARRAY(String(36)),
        nullable=True,
        default=[],
    )

    # Match scoring
    match_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    match_decision: Mapped[str | None] = mapped_column(String(50), nullable=True)
    matched_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Metadata
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    payment_terms: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_data: Mapped[dict | None] = mapped_column(Text, nullable=True)

    # Relationships
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    matched_po: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder",
        foreign_keys=[matched_po_id],
        back_populates="matched_invoices",
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} ({self.status.value})>"


class InvoiceLine(Base):
    """Invoice line item model.

    Represents individual line items on an invoice.
    """

    __tablename__ = "invoice_lines"
    __table_args__ = (
        Index("ix_invoice_lines_invoice_id", "invoice_id"),
        Index("ix_invoice_lines_line_number", "line_number"),
    )

    # Parent reference
    invoice_id: Mapped[UUID] = mapped_column(
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Line details
    line_number: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    # Quantities and amounts
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Matching references
    matched_po_line_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    matched_dn_line_ids: Mapped[list[UUID] | None] = mapped_column(
        ARRAY(String(36)),
        nullable=True,
        default=[],
    )
    match_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    match_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="lines")
    matched_po_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        foreign_keys=[matched_po_line_id],
        back_populates="matched_invoice_lines",
    )

    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number}: {self.description[:30]}>"


# Import at bottom to avoid circular imports
from models.purchase_order import PurchaseOrder, PurchaseOrderLine

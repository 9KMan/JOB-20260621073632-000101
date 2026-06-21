// models/invoice.py
"""Invoice and InvoiceLine SQLAlchemy models."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKey

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.delivery_note import DeliveryNote, DeliveryNoteLine
    from models.purchase_order import PurchaseOrder, PurchaseOrderLine


class Invoice(Base, UUIDPrimaryKey, TimestampMixin, SoftDeleteMixin):
    """Invoice header model.

    Represents an invoice document received from a supplier for goods or services.
    """

    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_supplier_number", "supplier_number"),
        Index("ix_invoices_invoice_date", "invoice_date"),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_erp_reference", "erp_reference"),
        UniqueConstraint("invoice_number", "supplier_number", name="uq_invoice_number_supplier"),
    )

    # Header Information
    invoice_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    supplier_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    supplier_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    supplier_tax_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    # Financial Information
    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    due_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
        index=True,
    )

    # ERP Reference
    erp_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    erp_sync_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
    )

    # Matching Information
    match_decision: Mapped[Optional[str]] = mapped_column(
        String(30),
        nullable=True,
    )
    match_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    match_confidence: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    matched_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Related PO (if anchored)
    purchase_order_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="invoices",
        lazy="selectin",
    )
    delivery_notes: Mapped[list["DeliveryNote"]] = relationship(
        "DeliveryNote",
        secondary="invoice_delivery_notes",
        back_populates="invoices",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} ({self.status})>"


class InvoiceLine(Base, UUIDPrimaryKey, TimestampMixin):
    """Invoice line item model.

    Represents individual line items on an invoice.
    """

    __tablename__ = "invoice_lines"
    __table_args__ = (
        Index("ix_invoice_lines_invoice_id", "invoice_id"),
        Index("ix_invoice_lines_line_number", "line_number"),
    )

    # Parent Invoice
    invoice_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Line Information
    line_number: Mapped[int] = mapped_column(
        nullable=False,
        index=True,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    # Product Information
    sku: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    product_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    barcode: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    # Quantity and Pricing
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="EA",
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    # Matching Status
    match_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
    )
    match_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    # Related PO Line (if matched)
    purchase_order_line_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Related Delivery Note Line (if matched)
    delivery_note_line_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
    )
    purchase_order_line: Mapped[Optional["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="invoice_lines",
    )
    delivery_note_line: Mapped[Optional["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="invoice_lines",
    )

    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number}: {self.description[:30]}>"


# Association table for invoice-delivery note many-to-many relationship
from sqlalchemy import Table, Column

invoice_delivery_notes = Table(
    "invoice_delivery_notes",
    Base.metadata,
    Column(
        "invoice_id",
        UUID(as_uuid=False),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "delivery_note_id",
        UUID(as_uuid=False),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "created_at",
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    ),
)

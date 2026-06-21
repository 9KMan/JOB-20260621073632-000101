// app/models/invoice.py
"""Invoice and InvoiceLine SQLAlchemy models."""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional

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
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from app.models.enums import InvoiceStatus


class Invoice(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """
    Invoice header model.
    
    Represents an accounts payable invoice received from vendors.
    """

    __tablename__ = "invoices"

    # Vendor information
    vendor_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    vendor_tax_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Invoice details
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    receipt_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Financial amounts
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")

    # Reference numbers
    purchase_order_ref: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    delivery_note_ref: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Processing status
    status: Mapped[InvoiceStatus] = mapped_column(
        String(20),
        nullable=False,
        default=InvoiceStatus.PENDING,
        index=True,
    )

    # Matching results
    match_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )
    match_decision: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    matched_po_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    matched_dn_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Exception tracking
    has_exception: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    exception_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    # Metadata
    payment_terms: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_system: Mapped[str] = mapped_column(String(50), nullable=False, default="manual")

    # Relationships
    lines: Mapped[List["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    matched_po: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        foreign_keys=[matched_po_id],
        backref="matched_invoices",
    )
    matched_dn: Mapped[Optional["DeliveryNote"]] = relationship(
        "DeliveryNote",
        foreign_keys=[matched_dn_id],
        backref="matched_invoices",
    )

    # Table indexes
    __table_args__ = (
        Index("ix_invoices_vendor_date", "vendor_id", "invoice_date"),
        Index("ix_invoices_status_created", "status", "created_at"),
        Index("ix_invoices_po_ref", "purchase_order_ref"),
    )

    def __repr__(self) -> str:
        return f"<Invoice(id={self.id}, number={self.invoice_number}, vendor={self.vendor_id})>"


class InvoiceLine(Base, UUIDMixin, TimestampMixin):
    """
    Invoice line item model.
    
    Represents individual line items on an invoice.
    """

    __tablename__ = "invoice_lines"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
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
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    quantity_received: Mapped[Decimal] = mapped_column(
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

    # Matching
    po_line_ref: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    dn_line_ref: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    matched_po_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("po_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    matched_dn_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dn_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    match_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)

    # Relationship
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="lines")
    matched_po_line: Mapped[Optional["POLine"]] = relationship(
        "POLine",
        foreign_keys=[matched_po_line_id],
        backref="matched_invoice_lines",
    )
    matched_dn_line: Mapped[Optional["DNLine"]] = relationship(
        "DNLine",
        foreign_keys=[matched_dn_line_id],
        backref="matched_invoice_lines",
    )

    __table_args__ = (
        Index("ix_invoice_lines_invoice_line", "invoice_id", "line_number"),
        Index("ix_invoice_lines_po_ref", "po_line_ref"),
    )

    def __repr__(self) -> str:
        return f"<InvoiceLine(id={self.id}, line={self.line_number}, product={self.product_code})>"


# Import for relationship resolution
from app.models.purchase_order import PurchaseOrder, POLine
from app.models.delivery_note import DeliveryNote, DNLine

// models/invoice.py
"""Invoice and InvoiceLine SQLAlchemy models."""

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from models.enums import DocumentStatus

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef


class Invoice(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Invoice model representing AP invoices."""

    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_vendor_number", "vendor_number"),
        Index("ix_invoices_invoice_number", "invoice_number", unique=True),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_invoice_date", "invoice_date"),
        Index("ix_invoices_created_at", "created_at"),
    )

    # Vendor Information
    vendor_number: Mapped[str] = mapped_column(String(50), nullable=False)
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    vendor_address: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Invoice Details
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    invoice_date: Mapped[Date] = mapped_column(Date, nullable=False)
    due_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    received_date: Mapped[Date] = mapped_column(Date, nullable=False)

    # Financial
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default=DocumentStatus.DRAFT.value,
        nullable=False,
    )
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ERP Reference
    erp_invoice_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_system: Mapped[str] = mapped_column(String(50), default="manual", nullable=False)

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} - {self.vendor_name}>"


class InvoiceLine(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Invoice line item model."""

    __tablename__ = "invoice_lines"
    __table_args__ = (
        Index("ix_invoice_lines_invoice_id", "invoice_id"),
        Index("ix_invoice_lines_line_number", "line_number"),
    )

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Line Details
    line_number: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Product Information
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    product_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    unit_of_measure: Mapped[str] = mapped_column(String(20), default="EA", nullable=False)

    # Quantities and Pricing
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tax_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    # Matching
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    matched_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        default=Decimal("0"),
        nullable=False,
    )
    match_status: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="lines")
    po_line: Mapped["PurchaseOrderLine | None"] = relationship(
        "PurchaseOrderLine",
        foreign_keys=[po_line_id],
        back_populates="matched_invoice_lines",
    )

    def __repr__(self) -> str:
        return f"<InvoiceLine {self.line_number}: {self.description[:30]}>"


from models.purchase_order import PurchaseOrderLine  # noqa: E402, F401

// models/invoice.py
"""Invoice model definition.

This module defines the Invoice SQLAlchemy model representing
incoming vendor invoices that need to be matched against POs.
"""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.enums import InvoiceStatusType

if TYPE_CHECKING:
    from models.balance_ledger import BalanceLedger
    from models.cross_ref import CrossRef


class Invoice(Base):
    """Invoice model representing vendor invoices.

    Attributes:
        id: UUID primary key
        invoice_number: Unique invoice number from vendor
        vendor_code: Vendor/supplier identifier
        vendor_name: Vendor name
        invoice_date: Date on the invoice
        due_date: Payment due date
        total_amount: Total invoice amount
        tax_amount: Tax amount (if applicable)
        currency: Currency code (ISO 4217)
        status: Current invoice status
        po_reference: Linked purchase order number (optional)
        notes: Additional notes
        is_ocr_processed: Whether OCR has been run on this invoice
        ocr_confidence: OCR confidence score (0-100)
        matched_at: Timestamp when invoice was matched
        approved_at: Timestamp when invoice was approved
        approved_by: User who approved the invoice
        created_at: Record creation timestamp
        updated_at: Record update timestamp
    """

    __tablename__ = "invoices"

    # Primary identification
    invoice_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique invoice number",
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
    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        doc="Invoice date",
    )
    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Payment due date",
    )

    # Financial amounts
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        doc="Total invoice amount",
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False,
        doc="Tax amount",
    )

    # Currency
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
        doc="Currency code (ISO 4217)",
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        default=InvoiceStatusType.RECEIVED.value,
        nullable=False,
        index=True,
        doc="Current invoice status",
    )

    # References
    po_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Reference to purchase order number",
    )

    # Notes
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Additional notes",
    )

    # OCR fields
    is_ocr_processed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether OCR has been processed",
    )
    ocr_confidence: Mapped[float] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
        doc="OCR confidence score (0-100)",
    )

    # Matching fields
    match_score: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        doc="Matching score (0-100)",
    )
    match_decision: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Match decision result",
    )

    # Approval fields
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Approval timestamp",
    )
    approved_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Approver user ID",
    )

    # Relationships
    balance_ledger_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )

    cross_refs: Mapped[list["CrossRef"]] = relationship(
        "CrossRef",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )

    # Table indexes
    __table_args__ = (
        Index("ix_invoices_vendor_date", "vendor_code", "invoice_date"),
        Index("ix_invoices_status_date", "status", "invoice_date"),
        Index("ix_invoices_po_reference", "po_reference"),
    )

    def __repr__(self) -> str:
        """String representation of Invoice."""
        return f"<Invoice(id={self.id}, number={self.invoice_number}, vendor={self.vendor_code}, amount={self.total_amount})>"

    @property
    def is_matched(self) -> bool:
        """Check if invoice is matched."""
        return self.status == InvoiceStatusType.MATCHED.value

    @property
    def is_approved(self) -> bool:
        """Check if invoice is approved."""
        return self.status == InvoiceStatusType.APPROVED.value

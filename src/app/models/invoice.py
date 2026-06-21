# src/app/models/invoice.py
"""Invoice models."""
import decimal
import uuid
from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DECIMAL, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from src.app.models.enums import DocumentStatus, LineStatus

if TYPE_CHECKING:
    from src.app.models.purchase_order import PurchaseOrderLine
    from src.app.models.delivery_note import DeliveryNoteLine
    from src.app.models.matching import MatchResult, CrossReference


class Invoice(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Invoice header."""
    
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("supplier_id", "invoice_number", name="uq_inv_supplier_inv"),
        {"schema": "documents"},
    )
    
    # Supplier reference
    supplier_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    supplier_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    # Invoice details
    invoice_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    invoice_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    due_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    
    # Financial
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )
    total_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
    )
    tax_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    
    # Status
    status: Mapped[DocumentStatus] = mapped_column(
        SQLEnum(DocumentStatus, name="document_status", create_type=False),
        default=DocumentStatus.RECEIVED,
        nullable=False,
        index=True,
    )
    
    # Metadata
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    metadata: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
    )
    
    # Relationships
    lines: Mapped[list["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    match_results: Mapped[list["MatchResult"]] = relationship(
        "MatchResult",
        back_populates="invoice",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<Invoice(id={self.id}, invoice_number={self.invoice_number})>"


class InvoiceLine(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Invoice Line item."""
    
    __tablename__ = "invoice_lines"
    __table_args__ = (
        UniqueConstraint("invoice_id", "line_number", name="uq_il_inv_line"),
        {"schema": "documents"},
    )
    
    # Foreign key
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Line details
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    sku: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    
    # Quantities and amounts
    quantity_invoiced: Mapped[decimal.Decimal] = mapped_column(
        Numeric(precision=12, scale=3),
        nullable=False,
    )
    unit_price: Mapped[decimal.Decimal] = mapped_column(
        Numeric(precision=12, scale=4),
        nullable=False,
    )
    line_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
    )
    
    # Status
    status: Mapped[LineStatus] = mapped_column(
        SQLEnum(LineStatus, name="line_status", create_type=False),
        default=LineStatus.PENDING,
        nullable=False,
    )
    
    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="lines",
    )
    cross_references: Mapped[list["CrossReference"]] = relationship(
        "CrossReference",
        back_populates="invoice_line",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<InvoiceLine(id={self.id}, line_number={self.line_number})>"

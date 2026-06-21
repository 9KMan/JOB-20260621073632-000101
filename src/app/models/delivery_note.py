# src/app/models/delivery_note.py
"""Delivery Note models."""
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
    from src.app.models.invoice import InvoiceLine
    from src.app.models.matching import MatchResult, CrossReference


class DeliveryNote(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Delivery Note header."""
    
    __tablename__ = "delivery_notes"
    __table_args__ = (
        UniqueConstraint("supplier_id", "dn_number", name="uq_dn_supplier_dn"),
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
    
    # DN details
    dn_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    dn_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    receipt_date: Mapped[Optional[date]] = mapped_column(
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
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    match_results: Mapped[list["MatchResult"]] = relationship(
        "MatchResult",
        back_populates="delivery_note",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<DeliveryNote(id={self.id}, dn_number={self.dn_number})>"


class DeliveryNoteLine(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Delivery Note Line item."""
    
    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        UniqueConstraint("dn_id", "line_number", name="uq_dnl_dn_line"),
        {"schema": "documents"},
    )
    
    # Foreign key
    dn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.delivery_notes.id", ondelete="CASCADE"),
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
    
    # Quantities
    quantity_delivered: Mapped[decimal.Decimal] = mapped_column(
        Numeric(precision=12, scale=3),
        nullable=False,
    )
    
    # Status
    status: Mapped[LineStatus] = mapped_column(
        SQLEnum(LineStatus, name="line_status", create_type=False),
        default=LineStatus.PENDING,
        nullable=False,
    )
    
    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )
    cross_references: Mapped[list["CrossReference"]] = relationship(
        "CrossReference",
        back_populates="dn_line",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<DeliveryNoteLine(id={self.id}, line_number={self.line_number})>"

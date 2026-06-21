// src/models/delivery_note.py
"""Delivery Note and Delivery Note Line models."""
import uuid
import decimal
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    String,
    Date,
    DateTime,
    Numeric,
    Integer,
    ForeignKey,
    Text,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel, SoftDeleteMixin
from src.models.enums import DocumentStatus

if TYPE_CHECKING:
    from src.models.supplier import Supplier
    from src.models.match import MatchLine, BalanceLedger


class DeliveryNote(BaseModel, SoftDeleteMixin):
    """Delivery Note / Goods Receipt from supplier."""

    __tablename__ = "delivery_notes"
    __table_args__ = (
        Index("ix_dn_supplier_status", "supplier_id", "status"),
        Index("ix_dn_number", "delivery_note_number"),
    )

    delivery_note_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    po_reference: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )
    delivery_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    received_by: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
    )
    status: Mapped[DocumentStatus] = mapped_column(
        DocumentStatus.enum,
        default=DocumentStatus.SUBMITTED,
        nullable=False,
    )
    subtotal: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )
    notes: Mapped[str] = mapped_column(
        Text,
        nullable=True,
    )
    attachment_url: Mapped[str] = mapped_column(
        String(500),
        nullable=True,
    )

    # Relationships
    supplier: Mapped["Supplier"] = relationship(
        "Supplier",
        back_populates="delivery_notes",
    )
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
    )
    matched_lines: Mapped[list["MatchLine"]] = relationship(
        "MatchLine",
        back_populates="delivery_note_line",
        foreign_keys="MatchLine.delivery_line_id",
    )
    balance_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="delivery_note",
        foreign_keys="BalanceLedger.delivery_note_id",
    )

    def calculate_totals(self) -> None:
        """Calculate subtotal from lines."""
        self.subtotal = sum((line.line_total for line in self.lines), decimal.Decimal("0.00"))

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.delivery_note_number}>"


class DeliveryNoteLine(BaseModel):
    """Delivery Note Line Item."""

    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_dnl_dn_line", "delivery_note_id", "line_number", unique=True),
    )

    delivery_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    product_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=True,
    )
    quantity_delivered: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    quantity_accepted: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=True,
    )
    quantity_rejected: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 4),
        default=decimal.Decimal("0.0000"),
        nullable=False,
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        default="EA",
        nullable=False,
    )
    unit_price: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    line_total: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )
    matched_lines: Mapped[list["MatchLine"]] = relationship(
        "MatchLine",
        back_populates="delivery_note_line",
        foreign_keys="MatchLine.delivery_line_id",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number}: {self.product_code}>"

    def calculate_totals(self) -> None:
        """Calculate line total from accepted quantity and unit price."""
        accepted_qty = self.quantity_accepted or self.quantity_delivered
        self.line_total = accepted_qty * self.unit_price

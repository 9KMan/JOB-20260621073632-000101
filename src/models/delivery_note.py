// src/models/delivery_note.py
"""Delivery Note models."""
import uuid
import decimal
from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String, Integer, Numeric, Date, DateTime, ForeignKey, Index, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import func

from src.models.base import Base, TimestampMixin, UUIDMixin, SoftDeleteMixin
from src.models.enums import DocumentStatus

if TYPE_CHECKING:
    from src.models.purchase_order import PurchaseOrderLine
    from src.models.invoice import InvoiceLine
    from src.models.matching import MatchRecord, BalanceLedger


class DeliveryNote(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Delivery Note model."""
    
    __tablename__ = "delivery_notes"
    __table_args__ = (
        Index("ix_dn_supplier_number", "supplier_id", "dn_number", unique=True),
        Index("ix_dn_status", "status"),
        Index("ix_dn_delivery_date", "delivery_date"),
        Index("ix_dn_po_id", "purchase_order_id"),
    )

    dn_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    supplier_id: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
    )
    supplier_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    supplier_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    delivery_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    received_by: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    total_quantity: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        default=decimal.Decimal("0.0000"),
    )
    total_lines: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    status: Mapped[DocumentStatus] = mapped_column(
        String(50),
        default=DocumentStatus.SUBMITTED,
        nullable=False,
        index=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
    )
    metadata: Mapped[Optional[str]] = mapped_column(
        String(2000),
        nullable=True,
    )

    # Relationships
    lines: Mapped[List["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        foreign_keys=[purchase_order_id],
    )
    matched_records: Mapped[List["MatchRecord"]] = relationship(
        "MatchRecord",
        back_populates="delivery_note",
        foreign_keys="MatchRecord.delivery_note_id",
    )
    balance_ledger: Mapped[List["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="delivery_note",
        foreign_keys="BalanceLedger.delivery_note_id",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote {self.dn_number}>"


class DeliveryNoteLine(Base, UUIDMixin, TimestampMixin):
    """Delivery Note Line Item model."""
    
    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_dnl_dn_line", "delivery_note_id", "line_number", unique=True),
    )

    delivery_note_id: Mapped[uuid.UUID] = mapped_column(
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
        nullable=True,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
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
    is_matched: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    matched_quantity: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 4),
        default=decimal.Decimal("0.0000"),
        nullable=False,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines",
    )
    matched_records: Mapped[List["MatchRecord"]] = relationship(
        "MatchRecord",
        back_populates="delivery_note_line",
        foreign_keys="MatchRecord.delivery_note_line_id",
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine {self.line_number}: {self.product_code}>"

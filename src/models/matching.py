// src/models/matching.py
"""Matching models for 3-way matching."""
import uuid
import decimal
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import String, Integer, Numeric, Date, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import func

from src.models.base import Base, TimestampMixin, UUIDMixin
from src.models.enums import MatchStatus, MatchDecision, DocumentType

if TYPE_CHECKING:
    from src.models.purchase_order import PurchaseOrder, PurchaseOrderLine
    from src.models.invoice import Invoice, InvoiceLine
    from src.models.delivery_note import DeliveryNote, DeliveryNoteLine
    from src.models.user import User


class MatchRecord(Base, UUIDMixin, TimestampMixin):
    """Record of a match between documents (3-way matching)."""
    
    __tablename__ = "match_records"
    __table_args__ = (
        Index("ix_mr_invoice_dn", "invoice_id", "delivery_note_id"),
        Index("ix_mr_invoice_po", "invoice_id", "purchase_order_id"),
        Index("ix_mr_dn_po", "delivery_note_id", "purchase_order_id"),
        Index("ix_mr_status", "status"),
        Index("ix_mr_decision", "decision"),
    )

    # Document references (at least two must be present for a valid match)
    invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    invoice_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("invoice_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    delivery_note_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    delivery_note_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    purchase_order_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Match details
    match_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    matched_quantity: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    matched_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    
    # Scoring
    line_match_score: Mapped[decimal.Decimal] = mapped_column(
        Numeric(5, 4),
        default=decimal.Decimal("0.0000"),
        nullable=False,
    )
    amount_match_score: Mapped[decimal.Decimal] = mapped_column(
        Numeric(5, 4),
        default=decimal.Decimal("0.0000"),
        nullable=False,
    )
    date_match_score: Mapped[decimal.Decimal] = mapped_column(
        Numeric(5, 4),
        default=decimal.Decimal("0.0000"),
        nullable=False,
    )
    total_match_score: Mapped[decimal.Decimal] = mapped_column(
        Numeric(5, 4),
        default=decimal.Decimal("0.0000"),
        nullable=False,
    )

    # Decision
    status: Mapped[MatchStatus] = mapped_column(
        String(50),
        default=MatchStatus.PENDING,
        nullable=False,
        index=True,
    )
    decision: Mapped[Optional[MatchDecision]] = mapped_column(
        String(50),
        nullable=True,
    )
    decision_reason: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    decided_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    decided_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Variance tracking
    quantity_variance: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 4),
        default=decimal.Decimal("0.0000"),
        nullable=False,
    )
    amount_variance: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    invoice: Mapped[Optional["Invoice"]] = relationship(
        "Invoice",
        back_populates="matched_records",
        foreign_keys=[invoice_id],
    )
    invoice_line: Mapped[Optional["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="matched_records",
        foreign_keys=[invoice_line_id],
    )
    delivery_note: Mapped[Optional["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="matched_records",
        foreign_keys=[delivery_note_id],
    )
    delivery_note_line: Mapped[Optional["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="matched_records",
        foreign_keys=[delivery_note_line_id],
    )
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="matched_invoice_lines",
        foreign_keys=[purchase_order_id],
    )
    purchase_order_line: Mapped[Optional["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="matched_invoice_lines",
        foreign_keys=[purchase_order_line_id],
    )
    confirmed_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[decided_by],
    )

    def __repr__(self) -> str:
        return f"<MatchRecord {self.id}: {self.match_type} - {self.status}>"


class MatchConfirmation(Base, UUIDMixin, TimestampMixin):
    """Confirmation record for human-reviewed matches (learning loop)."""
    
    __tablename__ = "match_confirmations"
    __table_args__ = (
        Index("ix_mc_match_record_id", "match_record_id", unique=True),
    )

    match_record_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("match_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    confirmed_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    confirmation_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    original_match_score: Mapped[decimal.Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
    )
    confirmation_notes: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    # Relationships
    match_record: Mapped["MatchRecord"] = relationship(
        "MatchRecord",
        foreign_keys=[match_record_id],
    )
    confirmed_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="match_confirmations",
        foreign_keys=[confirmed_by],
    )

    def __repr__(self) -> str:
        return f"<MatchConfirmation {self.id}>"


class BalanceLedger(Base, UUIDMixin, TimestampMixin):
    """Ledger to track partial matches and balances across all document types."""
    
    __tablename__ = "balance_ledger"
    __table_args__ = (
        Index("ix_bl_document", "document_type", "document_id"),
        Index("ix_bl_po_line", "purchase_order_id", "purchase_order_line_id"),
        Index("ix_bl_outstanding", "is_outstanding"),
    )

    document_type: Mapped[DocumentType] = mapped_column(
        String(50),
        nullable=False,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        nullable=False,
        index=True,
    )
    document_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        nullable=True,
        index=True,
    )

    # PO references (for 3-way balance tracking)
    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    purchase_order_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Invoice references
    invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    invoice_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("invoice_lines.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Delivery Note references
    delivery_note_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    delivery_note_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("delivery_note_lines.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Balance tracking
    original_quantity: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )
    matched_quantity: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 4),
        default=decimal.Decimal("0.0000"),
        nullable=False,
    )
    outstanding_quantity: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
    )

    original_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )
    matched_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    outstanding_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    is_outstanding: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
        index=True,
    )
    last_match_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    # Relationships
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="balance_ledger",
        foreign_keys=[purchase_order_id],
    )

    def __repr__(self) -> str:
        return f"<BalanceLedger {self.document_type}: {self.outstanding_amount}>"

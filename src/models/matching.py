# src/models/matching.py
import enum
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean, Date, DateTime, Enum, ForeignKey, Index, Numeric, String, Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.user import User
    from src.models.purchase_order import PurchaseOrder, PurchaseOrderLine
    from src.models.invoice import Invoice, InvoiceLine
    from src.models.delivery_note import DeliveryNote, DeliveryNoteLine


class MatchStatus(str, enum.Enum):
    """Status of individual matches."""
    PENDING = "pending"
    MATCHED = "matched"
    PARTIAL = "partial"
    UNMATCHED = "unmatched"


class DecisionStatus(str, enum.Enum):
    """Decision status for the matching result."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"
    DISPUTED = "disputed"


class MatchingResult(BaseModel):
    """
    Result of 3-way matching between Invoice, Delivery Note, and Purchase Order.
    """
    __tablename__ = "matching_results"
    __table_args__ = (
        Index("ix_mr_invoice_id", "invoice_id"),
        Index("ix_mr_delivery_note_id", "delivery_note_id"),
        Index("ix_mr_purchase_order_id", "purchase_order_id"),
        Index("ix_mr_status", "status"),
        Index("ix_mr_decision_status", "decision_status"),
    )

    # Document IDs
    invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=True
    )
    delivery_note_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=True
    )
    purchase_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True
    )

    # Match scores (0.0 to 1.0)
    line_match_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), default=Decimal("0.0000"), nullable=False
    )
    amount_match_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), default=Decimal("0.0000"), nullable=False
    )
    date_match_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), default=Decimal("0.0000"), nullable=False
    )
    overall_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), default=Decimal("0.0000"), nullable=False
    )

    # Match amounts
    po_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0.00"), nullable=False
    )
    invoice_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0.00"), nullable=False
    )
    variance_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0.00"), nullable=False
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20), default=MatchStatus.PENDING.value, nullable=False
    )
    decision_status: Mapped[str] = mapped_column(
        String(20), default=DecisionStatus.PENDING.value, nullable=False
    )

    # Variance details
    variance_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Review information
    reviewed_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    review_comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Routing decision
    routing_decision: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    auto_approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    invoice: Mapped[Optional["Invoice"]] = relationship(
        "Invoice",
        back_populates="matched_pos",
        foreign_keys=[invoice_id]
    )
    delivery_note: Mapped[Optional["DeliveryNote"]] = relationship(
        "DeliveryNote",
        back_populates="matched_pos",
        foreign_keys=[delivery_note_id]
    )
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="matched_invoices",
        foreign_keys=[purchase_order_id]
    )
    reviewed_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="matching_results",
        foreign_keys=[reviewed_by_id]
    )
    lines: Mapped[list["MatchingLine"]] = relationship(
        "MatchingLine",
        back_populates="matching_result",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<MatchingResult(id={self.id}, score={self.overall_score}, decision={self.decision_status})>"


class MatchingLine(BaseModel):
    """
    Line-level matching details between document lines.
    """
    __tablename__ = "matching_lines"
    __table_args__ = (
        Index("ix_ml_matching_result_id", "matching_result_id"),
    )

    matching_result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matching_results.id", ondelete="CASCADE"),
        nullable=False
    )

    # Line references
    purchase_order_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=True
    )
    invoice_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="CASCADE"),
        nullable=True
    )
    delivery_note_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="CASCADE"),
        nullable=True
    )

    # Match details
    item_code: Mapped[str] = mapped_column(String(100), nullable=False)
    item_description: Mapped[str] = mapped_column(String(500), nullable=False)

    # Quantities
    po_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3), default=Decimal("0.000"), nullable=False
    )
    invoice_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3), default=Decimal("0.000"), nullable=False
    )
    delivery_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3), default=Decimal("0.000"), nullable=False
    )
    matched_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3), default=Decimal("0.000"), nullable=False
    )
    variance_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3), default=Decimal("0.000"), nullable=False
    )

    # Amounts
    po_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0.00"), nullable=False
    )
    invoice_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0.00"), nullable=False
    )
    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0.00"), nullable=False
    )
    variance_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0.00"), nullable=False
    )

    # Match score for this line
    line_match_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), default=Decimal("0.0000"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), default=MatchStatus.PENDING.value, nullable=False
    )

    # Relationships
    matching_result: Mapped["MatchingResult"] = relationship(
        "MatchingResult",
        back_populates="lines"
    )
    purchase_order_line: Mapped[Optional["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="matching_lines"
    )
    invoice_line: Mapped[Optional["InvoiceLine"]] = relationship(
        "InvoiceLine",
        back_populates="matching_lines"
    )
    delivery_note_line: Mapped[Optional["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="matching_lines"
    )

    def __repr__(self) -> str:
        return f"<MatchingLine(id={self.id}, item={self.item_code}, score={self.line_match_score})>"


class BalanceLedger(BaseModel):
    """
    Tracks partial matches and balances across all document types.
    Enables handling of partial shipments, split invoices, and multi-delivery scenarios.
    """
    __tablename__ = "balance_ledger"
    __table_args__ = (
        Index("ix_bl_purchase_order_id", "purchase_order_id"),
        Index("ix_bl_document_type", "document_type"),
        Index("ix_bl_document_id", "document_id"),
    )

    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False
    )
    purchase_order_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_order_lines.id", ondelete="CASCADE"),
        nullable=True
    )

    # Document tracking
    document_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'invoice', 'delivery_note'
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    document_number: Mapped[str] = mapped_column(String(50), nullable=False)

    # Balance tracking
    original_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0.00"), nullable=False
    )
    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0.00"), nullable=False
    )
    remaining_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0.00"), nullable=False
    )

    # Original quantity
    original_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3), default=Decimal("0.000"), nullable=False
    )
    matched_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3), default=Decimal("0.000"), nullable=False
    )
    remaining_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3), default=Decimal("0.000"), nullable=False
    )

    # Status
    is_settled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    settlement_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="balance_entries"
    )

    def __repr__(self) -> str:
        return f"<BalanceLedger(id={self.id}, doc={self.document_type}:{self.document_number}, remaining={self.remaining_amount})>"

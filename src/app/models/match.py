// src/app/models/match.py
"""Match model for 3-way matching."""

from decimal import Decimal
from enum import Enum
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class MatchStatus(str, Enum):
    """Match status enumeration."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"
    HUMAN_REVIEW = "human_review"


class MatchResult(str, Enum):
    """Match result enumeration."""

    FULL_MATCH = "full_match"
    PARTIAL_MATCH = "partial_match"
    NO_MATCH = "no_match"


class Match(BaseModel):
    """Match model for 3-way matching records."""

    __tablename__ = "matches"

    # Document references
    invoice_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    dn_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    po_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )

    # Match metadata
    match_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # invoice_po, dn_po, invoice_dn, three_way
    status: Mapped[MatchStatus] = mapped_column(
        SQLEnum(MatchStatus),
        default=MatchStatus.PENDING,
        nullable=False,
    )
    result: Mapped[MatchResult] = mapped_column(
        SQLEnum(MatchResult),
        default=MatchResult.NO_MATCH,
        nullable=False,
    )

    # Scoring
    overall_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
    )
    line_level_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
    )
    amount_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
    )
    date_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
    )

    # Amount comparisons
    invoice_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )
    dn_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )
    po_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )
    variance_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
    )

    # Match dates
    match_date: Mapped[Date] = mapped_column(Date, nullable=False)
    decision_date: Mapped[Date | None] = mapped_column(Date, nullable=True)

    # Notes and details
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    scoring_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Line-level matches
    lines: Mapped[list["MatchLine"]] = relationship(
        "MatchLine",
        back_populates="match",
        cascade="all, delete-orphan",
    )

    # Relationships
    invoice: Mapped["Invoice | None"] = relationship(
        "Invoice",
        foreign_keys=[invoice_id],
        back_populates="matches",
    )
    delivery_note: Mapped["DeliveryNote | None"] = relationship(
        "DeliveryNote",
        foreign_keys=[dn_id],
        back_populates="matches",
    )
    purchase_order: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder",
        foreign_keys=[po_id],
        back_populates="invoice_matches",
    )
    purchase_order_for_dn: Mapped["PurchaseOrder | None"] = relationship(
        "PurchaseOrder",
        foreign_keys=[po_id],
        back_populates="delivery_note_matches",
    )

    def __repr__(self) -> str:
        return f"<Match {self.match_type} - {self.status}>"


class MatchLine(BaseModel):
    """Match Line model for line-level matching."""

    __tablename__ = "match_lines"

    match_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("matches.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Line references
    invoice_line_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    dn_line_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    po_line_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("po_lines.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Matching details
    match_type: Mapped[str] = mapped_column(String(50), nullable=False)
    score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
    )
    quantity_match: Mapped[bool] = mapped_column(default=False)
    price_match: Mapped[bool] = mapped_column(default=False)
    product_match: Mapped[bool] = mapped_column(default=False)

    # Quantities
    invoice_quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
    )
    dn_quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
    )
    po_quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
    )
    matched_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0.00"),
    )

    # Amounts
    invoice_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )
    po_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )
    variance_quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        default=Decimal("0.00"),
    )
    variance_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
    )

    # Relationships
    match: Mapped["Match"] = relationship(
        "Match",
        back_populates="lines",
    )
    invoice_line: Mapped["InvoiceLine | None"] = relationship(
        "InvoiceLine",
        back_populates="matched_lines",
    )
    dn_line: Mapped["DeliveryNoteLine | None"] = relationship(
        "DeliveryNoteLine",
        back_populates="matched_lines",
    )
    po_line: Mapped["POLine | None"] = relationship(
        "POLine",
        back_populates="matched_lines",
    )

    def __repr__(self) -> str:
        return f"<MatchLine {self.match_type} - Score: {self.score}>"


# Import at bottom to avoid circular imports
from app.models.invoice import Invoice, InvoiceLine
from app.models.delivery_note import DeliveryNote, DeliveryNoteLine
from app.models.purchase_order import PurchaseOrder, POLine

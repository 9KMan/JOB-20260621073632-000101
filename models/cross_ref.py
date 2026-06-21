# models/cross_ref.py
"""Cross Reference SQLAlchemy model.

Stores learned associations between invoices, POs, and delivery notes.
Implements the learning loop for the matching engine.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

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

from models.base import Base
from models.enums import CrossRefStatus

if TYPE_CHECKING:
    from models.invoice import Invoice, InvoiceLine


class CrossRef(Base):
    """Cross Reference model for learning loop.

    Records confirmed matches between entities to improve future matching.
    Tracks learned associations and promotes reliable patterns.
    """

    __tablename__ = "cross_ref"
    __table_args__ = (
        Index("ix_cross_ref_invoice_id", "invoice_id"),
        Index("ix_cross_ref_po_id", "po_id"),
        Index("ix_cross_ref_dn_id", "dn_id"),
        Index("ix_cross_ref_status", "status"),
        Index("ix_cross_ref_confirmed_count", "confirmed_count"),
        Index("ix_cross_ref_last_confirmed", "last_confirmed_at"),
        {"schema": None},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )
    invoice_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoice_lines.id", ondelete="CASCADE"),
        nullable=True,
    )
    po_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=True,
    )
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("po_lines.id", ondelete="CASCADE"),
        nullable=True,
    )
    dn_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=True,
    )
    dn_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_note_lines.id", ondelete="CASCADE"),
        nullable=True,
    )
    status: Mapped[CrossRefStatus] = mapped_column(
        String(30),
        default=CrossRefStatus.PENDING,
        nullable=False,
    )
    match_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    match_type: Mapped[str] = mapped_column(String(50), nullable=True)
    confirmed_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    rejected_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    reliability_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        default=Decimal("0.0000"),
        nullable=False,
    )
    first_confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    expires_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    match_metadata: Mapped[dict | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_auto_promoted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship(
        "Invoice",
        back_populates="cross_refs",
    )

    def __repr__(self) -> str:
        return f"<CrossRef {self.id}: score={self.match_score}, status={self.status}>"

    @property
    def is_promoted(self) -> bool:
        """Check if this cross-reference has been promoted."""
        return self.status == CrossRefStatus.PROMOTED

    @property
    def promotion_eligible(self) -> bool:
        """Check if this cross-reference is eligible for promotion."""
        return (
            self.confirmed_count >= 3
            and self.reliability_score >= Decimal("0.80")
            and self.status == CrossRefStatus.LEARNED
        )

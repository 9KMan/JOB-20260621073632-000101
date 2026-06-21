# models/cross_ref.py
"""CrossRef SQLAlchemy model for learning/promotion functionality."""

import uuid
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin
from models.enums import LearningStatus


class CrossRef(Base, TimestampMixin):
    """Cross-reference table for learning/promotion of matches.

    Stores learned associations between product codes, supplier parts,
    and PO numbers to improve future match accuracy. Acts as a
    "learning loop" that promotes confirmed matches.
    """

    __tablename__ = "cross_refs"

    # Product references
    vendor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    product_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    supplier_part_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    # PO reference
    po_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    po_line_number: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    # Learned values
    expected_unit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
    )
    expected_quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 4),
        nullable=True,
    )

    # Learning metrics
    match_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )
    success_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )
    failure_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )
    confirmation_rate: Mapped[float] = mapped_column(
        default=0.0,
        nullable=False,
    )

    # Status and priority
    status: Mapped[LearningStatus] = mapped_column(
        default=LearningStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    priority: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )
    is_verified: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    # Relationships
    promoted_by_invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
    )
    promoted_by_user_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    __table_args__ = (
        Index("ix_cross_refs_vendor_product", "vendor_id", "product_code", unique=True),
        Index("ix_cross_refs_vendor_supplier", "vendor_id", "supplier_part_number"),
        Index("ix_cross_refs_po_number", "po_number"),
        Index("ix_cross_refs_status_rate", "status", "confirmation_rate"),
    )

    def __repr__(self) -> str:
        return (
            f"<CrossRef {self.vendor_id}:{self.product_code} - "
            f"Rate: {self.confirmation_rate:.2%}>"
        )

    def update_success(self) -> None:
        """Record a successful match using this cross-reference."""
        self.success_count += 1
        self.match_count += 1
        self._recalculate_rate()

    def update_failure(self) -> None:
        """Record a failed match using this cross-reference."""
        self.failure_count += 1
        self.match_count += 1
        self._recalculate_rate()

    def _recalculate_rate(self) -> None:
        """Recalculate confirmation rate."""
        if self.match_count > 0:
            self.confirmation_rate = self.success_count / self.match_count
        else:
            self.confirmation_rate = 0.0

    def promote(self) -> None:
        """Promote this cross-reference to verified status."""
        self.status = LearningStatus.PROMOTED
        self.is_verified = True
        self.priority += 1

    def demote(self) -> None:
        """Demote this cross-reference."""
        self.status = LearningStatus.DEMOTED
        self.priority = max(0, self.priority - 1)

    @classmethod
    def create_from_match(
        cls,
        vendor_id: str,
        product_code: str,
        po_number: str | None = None,
        po_line_number: int | None = None,
        supplier_part_number: str | None = None,
        unit_price: Decimal | None = None,
        quantity: Decimal | None = None,
    ) -> "CrossRef":
        """Create a new cross-reference from a confirmed match.

        Args:
            vendor_id: Vendor identifier.
            product_code: Product code.
            po_number: Optional PO number.
            po_line_number: Optional PO line number.
            supplier_part_number: Optional supplier part number.
            unit_price: Expected unit price.
            quantity: Expected quantity.

        Returns:
            CrossRef: New cross-reference instance.
        """
        return cls(
            vendor_id=vendor_id,
            product_code=product_code,
            po_number=po_number,
            po_line_number=po_line_number,
            supplier_part_number=supplier_part_number,
            expected_unit_price=unit_price,
            expected_quantity=quantity,
            match_count=1,
            success_count=1,
            confirmation_rate=1.0,
        )

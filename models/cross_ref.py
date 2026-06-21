// models/cross_ref.py
"""CrossRef SQLAlchemy model for the learning loop/cross-reference table."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKey

if TYPE_CHECKING:
    from models.purchase_order import PurchaseOrder, PurchaseOrderLine


class CrossRef(Base, UUIDPrimaryKey, TimestampMixin):
    """Cross-Reference model for the learning loop.

    This table stores learned associations between suppliers, products,
    and purchase orders for improving matching accuracy over time.
    """

    __tablename__ = "cross_ref"
    __table_args__ = (
        Index("ix_cr_supplier_number", "supplier_number"),
        Index("ix_cr_sku", "sku"),
        Index("ix_cr_product_code", "product_code"),
        Index("ix_cr_status", "status"),
        Index("ix_cr_match_count", "match_count"),
        UniqueConstraint(
            "supplier_number",
            "sku",
            "product_code",
            name="uq_cr_supplier_sku_product",
        ),
    )

    # Supplier Information
    supplier_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # Product Information
    sku: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    product_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )
    barcode: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    # Reference PO Line (for price/quantity learning)
    purchase_order_line_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("purchase_order_lines.id", ondelete="SET NULL"),
        nullable=True,
    )
    purchase_order_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Learned Values
    learned_unit_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 4),
        nullable=True,
    )
    learned_unit_of_measure: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    learned_delivery_days: Mapped[Optional[int]] = mapped_column(
        nullable=True,
    )

    # Statistics
    match_count: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )
    confirmation_count: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )
    rejection_count: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )

    # Confidence Scoring
    confidence_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    last_confirmed_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        index=True,
    )
    is_auto_match_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # Relationships
    purchase_order_line: Mapped[Optional["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="cross_refs",
    )
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="cross_refs",
    )

    def __repr__(self) -> str:
        return (
            f"<CrossRef supplier={self.supplier_number} "
            f"sku={self.sku} confidence={self.confidence_score}%"
        )

    def promote(self) -> None:
        """Promote this cross-reference to higher confidence."""
        self.status = "promoted"
        self.confirmation_count += 1
        self.update_confidence()

    def demote(self) -> None:
        """Demote this cross-reference due to rejections."""
        self.status = "demoted"
        self.rejection_count += 1
        self.update_confidence()

    def archive(self) -> None:
        """Archive this cross-reference."""
        self.status = "archived"
        self.is_auto_match_enabled = False

    def update_confidence(self) -> None:
        """Update confidence score based on match statistics."""
        total = self.confirmation_count + self.rejection_count
        if total > 0:
            self.confidence_score = Decimal(
                str(round((self.confirmation_count / total) * 100, 2))
            )
        else:
            self.confidence_score = Decimal("0.00")

// models/cross_ref.py
"""CrossRef SQLAlchemy model for learning/cross-reference data."""

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin
from models.enums import CrossRefType

if TYPE_CHECKING:
    from models.purchase_order import PurchaseOrderLine


class CrossRef(Base, UUIDMixin, TimestampMixin):
    """Cross Reference model for learning and confirmed match data.

    This table stores learned associations and confirmed matches to improve
    future matching accuracy. It acts as a knowledge base for the matching
    engine.

    Attributes:
        id: UUID primary key
        ref_type: Type of cross-reference
        supplier_id: Supplier identifier
        supplier_sku: Supplier's SKU
        supplier_description: Supplier's product description
        internal_sku: Internal/System SKU
        internal_description: Internal product description
        confidence_score: Confidence score for this match (0-100)
        match_count: Number of times this match was used
        last_matched_date: Last date this reference was used
        is_active: Whether this reference is currently active
        is_verified: Whether this reference has been manually verified
    """

    __tablename__ = "cross_refs"
    __table_args__ = (
        UniqueConstraint(
            "supplier_id",
            "supplier_sku",
            name="uq_cross_ref_supplier_sku",
        ),
        Index("ix_cross_refs_supplier_id", "supplier_id"),
        Index("ix_cross_refs_supplier_sku", "supplier_sku"),
        Index("ix_cross_refs_internal_sku", "internal_sku"),
        Index("ix_cross_refs_ref_type", "ref_type"),
        Index("ix_cross_refs_is_active", "is_active"),
        {"schema": None},
    )

    # Reference type
    ref_type: Mapped[CrossRefType] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        doc="Type of cross-reference",
    )

    # Supplier information
    supplier_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Supplier identifier",
    )
    supplier_sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Supplier's SKU or product code",
    )
    supplier_description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Supplier's product description",
    )
    supplier_unit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=15, scale=4),
        nullable=True,
        doc="Supplier's unit price",
    )

    # Internal/canonical information
    internal_sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Internal or canonical SKU",
    )
    internal_description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Internal product description",
    )
    internal_unit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=15, scale=4),
        nullable=True,
        doc="Internal standard price",
    )

    # Category mapping
    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Product category",
    )

    # Confidence and usage tracking
    confidence_score: Mapped[float] = mapped_column(
        Numeric(precision=5, scale=2),
        nullable=False,
        default=0.0,
        doc="Confidence score (0-100)",
    )
    match_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of times this match was used",
    )
    last_matched_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Last date this reference was used for matching",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        default=True,
        doc="Whether this reference is currently active",
    )
    is_verified: Mapped[bool] = mapped_column(
        default=False,
        doc="Whether this reference has been manually verified",
    )

    # Promotion tracking
    promoted_from_learned: Mapped[bool] = mapped_column(
        default=False,
        doc="Whether this was promoted from a learned to a verified reference",
    )
    promotion_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        doc="Date when this reference was promoted",
    )

    def __repr__(self) -> str:
        return (
            f"<CrossRef(id={self.id}, type={self.ref_type}, "
            f"supplier_sku={self.supplier_sku}, internal_sku={self.internal_sku})>"
        )

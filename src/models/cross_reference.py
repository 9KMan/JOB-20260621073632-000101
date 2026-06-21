// src/models/cross_reference.py
"""Cross Reference model for item code normalization."""
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.supplier import Supplier
    from src.models.user import User


class CrossReference(BaseModel):
    """Cross Reference - maps item codes across documents for matching."""
    
    __tablename__ = "cross_references"
    
    supplier_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    po_item_code: Mapped[Optional[str]] = mapped_column(
        String(length=50),
        nullable=True,
        index=True,
    )
    invoice_item_code: Mapped[Optional[str]] = mapped_column(
        String(length=50),
        nullable=True,
        index=True,
    )
    dn_item_code: Mapped[Optional[str]] = mapped_column(
        String(length=50),
        nullable=True,
        index=True,
    )
    normalized_po_item: Mapped[Optional[str]] = mapped_column(
        String(length=100),
        nullable=True,
    )
    normalized_inv_item: Mapped[Optional[str]] = mapped_column(
        String(length=100),
        nullable=True,
    )
    normalized_dn_item: Mapped[Optional[str]] = mapped_column(
        String(length=100),
        nullable=True,
    )
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=5, scale=2),
        nullable=True,
    )
    usage_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    verified_by: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    supplier: Mapped[Optional["Supplier"]] = relationship(
        "Supplier",
        back_populates="cross_references",
    )
    verified_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[verified_by],
    )
    
    def __repr__(self) -> str:
        return f"<CrossReference {self.po_item_code} -> {self.invoice_item_code}>"

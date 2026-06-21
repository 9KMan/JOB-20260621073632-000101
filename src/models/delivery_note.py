# src/models/delivery_note.py
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean, Date, DateTime, ForeignKey, Index, Numeric, String, Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.matching import MatchingResult, MatchingLine


class DeliveryNote(BaseModel):
    """
    Delivery Note (Goods Received Note) model for AP matching.
    """
    __tablename__ = "delivery_notes"
    __table_args__ = (
        Index("ix_dn_supplier_dn_number", "supplier_id", "dn_number", unique=True),
        Index("ix_dn_supplier_id", "supplier_id"),
        Index("ix_dn_status", "status"),
        Index("ix_dn_delivery_date", "delivery_date"),
    )

    dn_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    supplier_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    supplier_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    delivery_date: Mapped[date] = mapped_column(Date, nullable=False)
    received_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    total_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 3), default=Decimal("0.000"), nullable=False)
    total_items: Mapped[int] = mapped_column(default=0, nullable=False)
    
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    lines: Mapped[list["DeliveryNoteLine"]] = relationship(
        "DeliveryNoteLine",
        back_populates="delivery_note",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    matched_pos: Mapped[list["MatchingResult"]] = relationship(
        "MatchingResult",
        back_populates="delivery_note",
        foreign_keys="MatchingResult.delivery_note_id"
    )

    def __repr__(self) -> str:
        return f"<DeliveryNote(id={self.id}, dn_number={self.dn_number}, supplier={self.supplier_id})>"


class DeliveryNoteLine(BaseModel):
    """
    Individual line items in a Delivery Note.
    """
    __tablename__ = "delivery_note_lines"
    __table_args__ = (
        Index("ix_dnl_delivery_note_id", "delivery_note_id"),
    )

    delivery_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("delivery_notes.id", ondelete="CASCADE"),
        nullable=False
    )
    
    line_number: Mapped[int] = mapped_column(nullable=False)
    item_code: Mapped[str] = mapped_column(String(100), nullable=False)
    item_description: Mapped[str] = mapped_column(String(500), nullable=False)
    
    quantity_delivered: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    quantity_accepted: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=True)
    quantity_rejected: Mapped[Decimal] = mapped_column(Numeric(15, 3), default=Decimal("0.000"), nullable=False)
    
    unit_of_measure: Mapped[str] = mapped_column(String(20), default="EA", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    delivery_note: Mapped["DeliveryNote"] = relationship(
        "DeliveryNote",
        back_populates="lines"
    )
    matching_lines: Mapped[list["MatchingLine"]] = relationship(
        "MatchingLine",
        back_populates="delivery_note_line"
    )

    def __repr__(self) -> str:
        return f"<DeliveryNoteLine(id={self.id}, line_number={self.line_number}, item={self.item_code})>"

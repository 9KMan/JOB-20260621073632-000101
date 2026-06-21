# src/models/purchase_order.py
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
    from src.models.matching import MatchingResult, MatchingLine, BalanceLedger


class PurchaseOrder(BaseModel):
    """
    Purchase Order model - the single source of truth in the 3-way matching.
    """
    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_po_supplier_po_number", "supplier_id", "po_number", unique=True),
        Index("ix_po_supplier_id", "supplier_id"),
        Index("ix_po_status", "status"),
        Index("ix_po_created_at", "created_at"),
    )

    po_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    supplier_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    supplier_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    supplier_tax_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    matched_invoices: Mapped[list["MatchingResult"]] = relationship(
        "MatchingResult",
        back_populates="purchase_order",
        foreign_keys="MatchingResult.purchase_order_id"
    )
    balance_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="purchase_order",
        foreign_keys="BalanceLedger.purchase_order_id"
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder(id={self.id}, po_number={self.po_number}, supplier={self.supplier_id})>"


class PurchaseOrderLine(BaseModel):
    """
    Individual line items in a Purchase Order.
    """
    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        Index("ix_pol_purchase_order_id", "purchase_order_id"),
    )

    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False
    )
    
    line_number: Mapped[int] = mapped_column(nullable=False)
    item_code: Mapped[str] = mapped_column(String(100), nullable=False)
    item_description: Mapped[str] = mapped_column(String(500), nullable=False)
    
    quantity_ordered: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    quantity_delivered: Mapped[Decimal] = mapped_column(Numeric(15, 3), default=Decimal("0.000"), nullable=False)
    quantity_remaining: Mapped[Decimal] = mapped_column(Numeric(15, 3), nullable=False)
    
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    line_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    
    tax_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines"
    )
    matching_lines: Mapped[list["MatchingLine"]] = relationship(
        "MatchingLine",
        back_populates="purchase_order_line"
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine(id={self.id}, line_number={self.line_number}, item={self.item_code})>"

// src/models/purchase_order.py
"""Purchase Order and Line models."""
from decimal import Decimal
from sqlalchemy import String, Numeric, Integer, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional, TYPE_CHECKING

from src.models.base import BaseModel
from src.models.enums import DocumentStatus, document_status_enum

if TYPE_CHECKING:
    from src.models.supplier import Supplier
    from src.models.invoice import Invoice
    from src.models.delivery_note import DeliveryNote
    from src.models.matching import Match, BalanceEntry


class PurchaseOrder(BaseModel):
    """Purchase Order header model."""
    
    __tablename__ = "purchase_orders"
    
    po_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )
    
    supplier_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    
    order_date: Mapped[date] = mapped_column(
        Date(timezone=True),
        nullable=False,
        index=True
    )
    
    expected_delivery_date: Mapped[Optional[date]] = mapped_column(
        Date(timezone=True),
        nullable=True
    )
    
    status: Mapped[DocumentStatus] = mapped_column(
        document_status_enum,
        default=DocumentStatus.DRAFT,
        nullable=False,
        index=True
    )
    
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False
    )
    
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False
    )
    
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False
    )
    
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        default=Decimal("0.00"),
        nullable=False
    )
    
    notes: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True
    )
    
    # Relationships
    supplier: Mapped["Supplier"] = relationship(
        "Supplier",
        back_populates="purchase_orders"
    )
    
    lines: Mapped[List["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="joined"
    )
    
    matched_invoices: Mapped[List["Match"]] = relationship(
        "Match",
        back_populates="purchase_order",
        foreign_keys="Match.po_id",
        lazy="dynamic"
    )
    
    balance_entries: Mapped[List["BalanceEntry"]] = relationship(
        "BalanceEntry",
        back_populates="purchase_order",
        foreign_keys="BalanceEntry.po_id",
        lazy="dynamic"
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_purchase_orders_supplier_status", "supplier_id", "status"),
        Index("ix_purchase_orders_order_date", "order_date"),
    )
    
    def __repr__(self) -> str:
        return f"<PurchaseOrder(id={self.id}, po_number={self.po_number})>"


class PurchaseOrderLine(BaseModel):
    """Purchase Order line item model."""
    
    __tablename__ = "purchase_order_lines"
    
    purchase_order_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    
    product_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )
    
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )
    
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False
    )
    
    unit_of_measure: Mapped[str] = mapped_column(
        String(20),
        default="EA",
        nullable=False
    )
    
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False
    )
    
    line_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False
    )
    
    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines"
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_purchase_order_lines_po_product", "purchase_order_id", "product_code"),
    )
    
    def __repr__(self) -> str:
        return f"<PurchaseOrderLine(id={self.id}, line_number={self.line_number}, product={self.product_code})>"

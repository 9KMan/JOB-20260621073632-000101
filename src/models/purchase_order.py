// src/models/purchase_order.py
"""Purchase Order models."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Integer, Numeric, Date, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel, SoftDeleteMixin

if TYPE_CHECKING:
    from src.models.matching import MatchRecord
    from src.models.balance import BalanceLedger


class PurchaseOrder(BaseModel, SoftDeleteMixin):
    """Purchase Order - Single source of truth for 3-way matching."""
    
    __tablename__ = "purchase_orders"
    
    po_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )
    
    supplier_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )
    
    supplier_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="OPEN"
    )
    
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD"
    )
    
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False
    )
    
    order_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )
    
    expected_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True
    )
    
    # Relationships
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        order_by="PurchaseOrderLine.line_number"
    )
    
    match_records: Mapped[list["MatchRecord"]] = relationship(
        "MatchRecord",
        back_populates="purchase_order"
    )
    
    balance_entries: Mapped[list["BalanceLedger"]] = relationship(
        "BalanceLedger",
        back_populates="purchase_order",
        foreign_keys="BalanceLedger.document_id",
        primaryjoin="and_(PurchaseOrder.id==BalanceLedger.document_id, BalanceLedger.document_type=='purchase_order')"
    )
    
    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.po_number}>"
    
    @property
    def open_amount(self) -> Decimal:
        """Calculate remaining open amount."""
        from sqlalchemy import select, func as sql_func
        from src.models.balance import BalanceLedger
        
        # This would be computed via a query in practice
        return self.total_amount


class PurchaseOrderLine(BaseModel):
    """Individual line item in a Purchase Order."""
    
    __tablename__ = "purchase_order_lines"
    
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    
    sku: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    
    quantity_ordered: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        nullable=False
    )
    
    quantity_received: Mapped[Decimal] = mapped_column(
        Numeric(15, 3),
        default=Decimal("0")
    )
    
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False
    )
    
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False
    )
    
    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines"
    )
    
    def __repr__(self) -> str:
        return f"<PurchaseOrderLine {self.line_number}: {self.sku}>"
    
    @property
    def quantity_pending(self) -> Decimal:
        """Calculate pending quantity."""
        return self.quantity_ordered - self.quantity_received

# src/app/models/purchase_order.py
"""Purchase Order models."""
import decimal
import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DECIMAL, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin
from src.app.models.enums import DocumentStatus, LineStatus

if TYPE_CHECKING:
    from src.app.models.invoice import InvoiceLine
    from src.app.models.delivery_note import DeliveryNoteLine
    from src.app.models.matching import MatchResult, CrossReference


class PurchaseOrder(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Purchase Order header."""
    
    __tablename__ = "purchase_orders"
    __table_args__ = (
        UniqueConstraint("supplier_id", "po_number", name="uq_po_supplier_po"),
        {"schema": "documents"},
    )
    
    # Supplier reference
    supplier_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    supplier_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    # PO details
    po_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    po_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    
    # Financial
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )
    total_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
    )
    tax_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        default=decimal.Decimal("0.00"),
        nullable=False,
    )
    
    # Status
    status: Mapped[DocumentStatus] = mapped_column(
        SQLEnum(DocumentStatus, name="document_status", create_type=False),
        default=DocumentStatus.OPEN,
        nullable=False,
        index=True,
    )
    
    # Metadata
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    metadata: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
    )
    
    # Relationships
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    matched_invoices: Mapped[list["MatchResult"]] = relationship(
        "MatchResult",
        foreign_keys="MatchResult.po_id",
        back_populates="purchase_order",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<PurchaseOrder(id={self.id}, po_number={self.po_number})>"


class PurchaseOrderLine(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Purchase Order Line item."""
    
    __tablename__ = "purchase_order_lines"
    __table_args__ = (
        UniqueConstraint("po_id", "line_number", name="uq_pol_po_line"),
        {"schema": "documents"},
    )
    
    # Foreign key
    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Line details
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    sku: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    
    # Quantities and amounts
    quantity_ordered: Mapped[decimal.Decimal] = mapped_column(
        Numeric(precision=12, scale=3),
        nullable=False,
    )
    quantity_delivered: Mapped[decimal.Decimal] = mapped_column(
        Numeric(precision=12, scale=3),
        default=decimal.Decimal("0.000"),
        nullable=False,
    )
    quantity_invoiced: Mapped[decimal.Decimal] = mapped_column(
        Numeric(precision=12, scale=3),
        default=decimal.Decimal("0.000"),
        nullable=False,
    )
    unit_price: Mapped[decimal.Decimal] = mapped_column(
        Numeric(precision=12, scale=4),
        nullable=False,
    )
    line_amount: Mapped[decimal.Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False,
    )
    
    # Status
    status: Mapped[LineStatus] = mapped_column(
        SQLEnum(LineStatus, name="line_status", create_type=False),
        default=LineStatus.PENDING,
        nullable=False,
    )
    
    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
    )
    matched_invoice_lines: Mapped[list["CrossReference"]] = relationship(
        "CrossReference",
        foreign_keys="CrossReference.po_line_id",
        back_populates="po_line",
        lazy="selectin",
    )
    matched_dn_lines: Mapped[list["CrossReference"]] = relationship(
        "CrossReference",
        foreign_keys="CrossReference.dn_line_id",
        back_populates="dn_line",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<PurchaseOrderLine(id={self.id}, line_number={self.line_number})>"

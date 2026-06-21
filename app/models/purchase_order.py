# app/models/purchase_order.py
"""Purchase Order and Purchase Order Line models."""
from sqlalchemy import Column, String, Numeric, ForeignKey, Integer, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from app.models.base import Base, TimestampMixin


class POStatus(str, enum.Enum):
    """Purchase Order status enum."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class PurchaseOrder(Base, TimestampMixin):
    """Purchase Order model - Single source of truth in Layer 1."""

    __tablename__ = "purchase_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    po_number = Column(String(50), unique=True, nullable=False, index=True)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False)
    status = Column(String(20), default=POStatus.SUBMITTED.value, nullable=False, index=True)
    order_date = Column(String(20), nullable=False)  # ISO date string
    expected_delivery_date = Column(String(20), nullable=True)
    currency = Column(String(3), default="USD", nullable=False)
    subtotal = Column(Numeric(15, 2), default=0, nullable=False)
    tax_amount = Column(Numeric(15, 2), default=0, nullable=False)
    total_amount = Column(Numeric(15, 2), default=0, nullable=False)
    shipping_cost = Column(Numeric(15, 2), default=0, nullable=False)
    notes = Column(Text, nullable=True)
    terms_and_conditions = Column(Text, nullable=True)
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(String(30), nullable=True)

    # Relationships
    vendor = relationship("Vendor", back_populates="purchase_orders")
    lines = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )
    matched_invoices = relationship(
        "MatchingResult",
        foreign_keys="MatchingResult.po_id",
        back_populates="purchase_order",
    )
    matched_delivery_notes = relationship(
        "MatchingResult",
        foreign_keys="MatchingResult.dn_id",
        back_populates="delivery_note",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder(id={self.id}, po_number={self.po_number}, total={self.total_amount})>"


class PurchaseOrderLine(Base, TimestampMixin):
    """Purchase Order Line Item model."""

    __tablename__ = "purchase_order_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    purchase_order_id = Column(
        UUID(as_uuid=True), ForeignKey("purchase_order_lines.id", use_alter=True), nullable=True
    )
    po_id = Column(
        UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False
    )
    line_number = Column(Integer, nullable=False)
    product_code = Column(String(100), nullable=True, index=True)
    description = Column(Text, nullable=False)
    quantity = Column(Numeric(15, 4), default=0, nullable=False)
    unit_of_measure = Column(String(20), default="EA", nullable=False)
    unit_price = Column(Numeric(15, 4), default=0, nullable=False)
    line_total = Column(Numeric(15, 2), default=0, nullable=False)
    tax_rate = Column(Numeric(5, 4), default=0, nullable=False)
    expected_delivery_date = Column(String(20), nullable=True)

    # Relationships
    purchase_order = relationship(
        "PurchaseOrder",
        back_populates="lines",
        foreign_keys=[po_id],
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine(id={self.id}, line_number={self.line_number}, product={self.product_code})>"

    def calculate_line_total(self) -> None:
        """Calculate line total including tax."""
        self.line_total = (self.quantity * self.unit_price) * (1 + self.tax_rate)

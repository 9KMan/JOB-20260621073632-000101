// src/app/models/purchase_order.py
"""Purchase Order and Purchase Order Line models."""

from sqlalchemy import Column, String, Numeric, Integer, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from src.app.models.base import BaseModel


class PurchaseOrder(BaseModel):
    """Purchase Order header entity."""

    __tablename__ = "purchase_orders"

    po_number = Column(String(50), unique=True, nullable=False, index=True)
    supplier_id = Column(
        UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False
    )
    order_date = Column(Date, nullable=False)
    expected_delivery_date = Column(Date, nullable=True)
    total_amount = Column(Numeric(15, 2), nullable=False, default=0)
    currency = Column(String(3), nullable=False, default="USD")
    status = Column(String(20), nullable=False, default="OPEN")
    notes = Column(String(1000), nullable=True)

    # Relationships
    supplier = relationship("Supplier", back_populates="purchase_orders")
    lines = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder(id={self.id}, po_number={self.po_number})>"


class PurchaseOrderLine(BaseModel):
    """Purchase Order line item entity."""

    __tablename__ = "purchase_order_lines"

    purchase_order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    line_number = Column(Integer, nullable=False)
    item_code = Column(String(50), nullable=False)
    description = Column(String(500), nullable=True)
    quantity = Column(Numeric(12, 3), nullable=False)
    unit_price = Column(Numeric(15, 4), nullable=False)
    line_total = Column(Numeric(15, 2), nullable=False)
    uom = Column(String(20), nullable=True)

    # Relationships
    purchase_order = relationship("PurchaseOrder", back_populates="lines")

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine(id={self.id}, line_number={self.line_number})>"
